//! Port of `api_go/main.go`.
//!
//! Go's `panic` + `defer recover()` is replaced by `Result`: every handler body returns
//! `anyhow::Result`, and any `Err` is logged and answered with the empty payload
//! (HTTP 200), exactly like the Go `recover` branch.

mod aws;
mod db;

use std::collections::HashMap;
use std::path::Path;

use anyhow::{Context, Result, anyhow, bail};
use axum::Router;
use axum::body::Bytes;
use axum::extract::multipart::MultipartRejection;
use axum::extract::rejection::BytesRejection;
use axum::extract::{DefaultBodyLimit, Multipart, State};
use axum::http::{Method, header};
use axum::response::{IntoResponse, Response};
use axum::routing::any;
use chrono::{Local, NaiveDate};
use serde::Serialize;
use tracing_subscriber::EnvFilter;

const IMAGES_ROOT: &str = "/var/www/like-av.xyz/images/";
const LISTEN_ADDR: &str = "0.0.0.0:9090";
/// Go used `ParseMultipartForm(32 << 20)`; axum's default body limit is only 2 MB.
const UPLOAD_BODY_LIMIT: usize = 32 << 20;

#[derive(Clone)]
struct AppState {
    db: mongodb::Database,
    rekognition: aws_sdk_rekognition::Client,
}

/// Field names follow the Go struct (no json tags → PascalCase keys).
#[derive(Debug, Serialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
struct Payload {
    count: usize,
    file: String,
    /// `None` serialises as `null`, matching Go's nil slice in `emptyPayload`.
    data: Option<Vec<Face>>,
}

#[derive(Debug, Serialize, PartialEq)]
#[serde(rename_all = "PascalCase")]
struct Face {
    id: String,
    name: String,
    img: String,
    similarity: String,
}

impl Payload {
    fn empty() -> Self {
        Payload {
            count: 0,
            file: String::new(),
            data: None,
        }
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Default: our own logs at info, everything else (AWS SDK, mongodb, hyper...) at warn.
    // Override with RUST_LOG, e.g. RUST_LOG=api=debug or RUST_LOG=debug.
    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("api=info,warn")),
        )
        .init();

    let state = AppState {
        db: db::connect().await?,
        rekognition: aws::new_client().await,
    };

    let app = app(state);

    let listener = tokio::net::TcpListener::bind(LISTEN_ADDR)
        .await
        .with_context(|| format!("ListenAndServe: {LISTEN_ADDR}"))?;
    tracing::info!("listening on {LISTEN_ADDR}");
    axum::serve(listener, app).await?;
    Ok(())
}

fn app(state: AppState) -> Router {
    // `any` keeps Go's behaviour: wrong methods get the empty payload, not a 405.
    Router::new()
        .route(
            "/upload",
            any(upload_handler).layer(DefaultBodyLimit::max(UPLOAD_BODY_LIMIT)),
        )
        .route("/feedback", any(feedback_handler))
        .with_state(state)
}

/// Response with the CORS + JSON headers the Go handlers always set.
fn json_response(body: Vec<u8>) -> Response {
    (
        [
            (header::ACCESS_CONTROL_ALLOW_ORIGIN, "*"),
            (header::CONTENT_TYPE, "application/json"),
        ],
        body,
    )
        .into_response()
}

fn to_json(payload: &Payload) -> Vec<u8> {
    // Serialising these plain structs cannot fail.
    serde_json::to_vec(payload).unwrap_or_default()
}

/// The `recover()` branch: log the error and reply with the empty payload.
fn finish(result: Result<Vec<u8>>) -> Response {
    match result {
        Ok(body) => json_response(body),
        Err(err) => {
            tracing::error!("{err:#}");
            json_response(to_json(&Payload::empty()))
        }
    }
}

fn check_post(method: &Method) -> Result<()> {
    if method != Method::POST {
        bail!("Allowed POST method only");
    }
    Ok(())
}

async fn upload_handler(
    State(state): State<AppState>,
    method: Method,
    multipart: Result<Multipart, MultipartRejection>,
) -> Response {
    finish(upload(&state, &method, multipart).await)
}

async fn upload(
    state: &AppState,
    method: &Method,
    multipart: Result<Multipart, MultipartRejection>,
) -> Result<Vec<u8>> {
    check_post(method)?;
    let mut multipart = multipart?;

    // r.FormFile("upload"): the first file part named "upload".
    while let Some(field) = multipart.next_field().await? {
        if field.name() != Some("upload") {
            continue;
        }
        let Some(raw_name) = field.file_name() else {
            continue;
        };
        // Go's multipart.Part.FileName() returns filepath.Base of the client filename.
        let file_name = Path::new(raw_name)
            .file_name()
            .and_then(|n| n.to_str())
            .ok_or_else(|| anyhow!("invalid upload filename: {raw_name:?}"))?
            .to_string();
        let bytes = field.bytes().await?;
        return search_face(state, bytes.to_vec(), &file_name).await;
    }
    bail!("http: no such file")
}

async fn search_face(state: &AppState, bytes: Vec<u8>, file_name: &str) -> Result<Vec<u8>> {
    let Some(result) = aws::search_faces_by_image(&state.rekognition, bytes.clone()).await? else {
        tracing::info!(file_name, "upload: no match");
        return Ok(to_json(&Payload::empty()));
    };

    let today = Local::now().format("%Y-%m-%d").to_string();
    let image_dir = format!("{IMAGES_ROOT}{today}");
    // os.Mkdir: single level, error ignored (usually "already exists").
    let _ = tokio::fs::create_dir(&image_dir).await;
    let uuid = uuid::Uuid::new_v4().simple().to_string();
    let uuid_file_name = format!("{}_{file_name}", &uuid[..8]);
    tokio::fs::write(format!("{image_dir}/{uuid_file_name}"), &bytes)
        .await
        .context("failed to save uploaded image")?;

    let mut data = Vec::new();
    for matched in result.iter().take(2) {
        let similarity = format!("{:.2}", matched.similarity);
        let actress = db::find_one_actress(&state.db, &matched.id).await?;
        let Some(actress) = actress.filter(|a| !a.is_empty()) else {
            tracing::warn!(id = %matched.id, "upload: actress not found");
            return Ok(to_json(&Payload::empty()));
        };

        data.push(Face {
            id: matched.id.clone(),
            name: actress.get("name").cloned().unwrap_or_default(),
            img: actress.get("img").cloned().unwrap_or_default(),
            similarity,
        });
    }

    let file = format!("{today}/{uuid_file_name}");
    let faces = data
        .iter()
        .map(|f| format!("{}:{}:{}", f.id, f.name, f.similarity))
        .collect::<Vec<_>>()
        .join(", ");
    tracing::info!(%file, %faces, "upload");

    Ok(to_json(&Payload {
        count: data.len(),
        file,
        data: Some(data),
    }))
}

async fn feedback_handler(
    State(state): State<AppState>,
    method: Method,
    body: Result<Bytes, BytesRejection>,
) -> Response {
    finish(feedback(&state, &method, body).await)
}

async fn feedback(
    state: &AppState,
    method: &Method,
    body: Result<Bytes, BytesRejection>,
) -> Result<Vec<u8>> {
    check_post(method)?;
    // Decode regardless of Content-Type, like json.NewDecoder(r.Body).
    let val: HashMap<String, String> = serde_json::from_slice(&body?)?;
    let field = |k: &str| val.get(k).map(String::as_str).unwrap_or("");
    let id = field("id");
    let ox = db::Vote::parse(field("ox"))?;
    let file = validate_image_path(field("file"))?;

    if ox == db::Vote::Like {
        let bytes = tokio::fs::read(format!("{IMAGES_ROOT}{file}")).await?;
        aws::insert_index_face_by_image(&state.rekognition, id, bytes).await?;
    }

    db::upsert_one_feedback(&state.db, id, ox, file).await?;
    db::upsert_one_week_rank(&state.db, id).await?;
    tracing::info!(id, ox = ox.as_str(), file, "feedback");

    // Go wrote nothing on success: 200 with an empty body.
    Ok(Vec::new())
}

/// `file` must look exactly like what `/upload` returns: `YYYY-MM-DD/<8 hex>_<name>`,
/// i.e. one date directory plus one plain file name. This blocks path traversal
/// (`../`, absolute paths, nested dirs) when it is joined to `IMAGES_ROOT`.
fn validate_image_path(file: &str) -> Result<&str> {
    let invalid = || anyhow!("invalid file: {file:?}");
    let (date, name) = file.split_once('/').ok_or_else(invalid)?;

    let parsed = NaiveDate::parse_from_str(date, "%Y-%m-%d").map_err(|_| invalid())?;
    if parsed.format("%Y-%m-%d").to_string() != date {
        return Err(invalid());
    }

    // Check the ASCII prefix on raw bytes so multibyte names can't hit a char-boundary panic.
    let b = name.as_bytes();
    if b.len() < 10 || !b[..8].iter().all(u8::is_ascii_hexdigit) || b[8] != b'_' {
        return Err(invalid());
    }
    // Bytes 0..9 are ASCII, so index 9 is a char boundary.
    if name[9..].contains(['/', '\\', '\0']) {
        return Err(invalid());
    }
    Ok(file)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_payload_matches_go() {
        assert_eq!(
            String::from_utf8(to_json(&Payload::empty())).unwrap(),
            r#"{"Count":0,"File":"","Data":null}"#
        );
    }

    #[test]
    fn payload_matches_go() {
        let p = Payload {
            count: 1,
            file: "2026-11-23/abcd1234_a.jpg".into(),
            data: Some(vec![Face {
                id: "x".into(),
                name: "n".into(),
                img: "i".into(),
                similarity: format!("{:.2}", 98.5_f32),
            }]),
        };
        assert_eq!(
            String::from_utf8(to_json(&p)).unwrap(),
            r#"{"Count":1,"File":"2026-11-23/abcd1234_a.jpg","Data":[{"Id":"x","Name":"n","Img":"i","Similarity":"98.50"}]}"#
        );
    }

    #[test]
    fn image_path_accepts_upload_format() {
        assert!(validate_image_path("2026-11-23/abcd1234_photo.jpg").is_ok());
        // a single path component, so harmless
        assert!(validate_image_path("2026-11-23/abcd1234_..").is_ok());
    }

    #[test]
    fn image_path_rejects_traversal_and_junk() {
        for bad in [
            "",
            "../../etc/passwd",
            "2026-11-23/../../etc/passwd",
            "2026-11-23/abcd1234_a/../../x",
            "/etc/passwd",
            "2026-11-23//etc/passwd",
            "2026-1-1/abcd1234_a.jpg",
            "2026-13-01/abcd1234_a.jpg",
            "2026-11-23/abcd123_a.jpg",
            "2026-11-23/abcdxyz1_a.jpg",
            "2026-11-23/abcd1234_",
            "2026-11-23/abcd1234-a.jpg",
            "2026-11-23/abcd1234_a\\..\\x",
            "2026-11-23/日本語日本語日本語",
        ] {
            assert!(
                validate_image_path(bad).is_err(),
                "{bad:?} should be rejected"
            );
        }
    }

    // ---- handler-level: every failure path must be 200 + headers + empty payload ----

    use axum::body::Body;
    use axum::http::{Request, StatusCode};
    use tower::ServiceExt;

    async fn test_app() -> Router {
        // Neither client connects eagerly; these paths never reach Mongo or AWS.
        let client =
            mongodb::Client::with_options(mongodb::options::ClientOptions::default()).unwrap();
        app(AppState {
            db: client.database(db::DATABASE),
            rekognition: aws::new_client().await,
        })
    }

    async fn assert_empty_payload(req: Request<Body>) {
        let resp = test_app().await.oneshot(req).await.unwrap();
        assert_eq!(resp.status(), StatusCode::OK);
        assert_eq!(resp.headers()[header::ACCESS_CONTROL_ALLOW_ORIGIN], "*");
        assert_eq!(resp.headers()[header::CONTENT_TYPE], "application/json");
        let body = axum::body::to_bytes(resp.into_body(), usize::MAX)
            .await
            .unwrap();
        assert_eq!(&body[..], br#"{"Count":0,"File":"","Data":null}"#);
    }

    #[tokio::test]
    async fn get_upload() {
        assert_empty_payload(Request::get("/upload").body(Body::empty()).unwrap()).await;
    }

    #[tokio::test]
    async fn get_feedback() {
        assert_empty_payload(Request::get("/feedback").body(Body::empty()).unwrap()).await;
    }

    #[tokio::test]
    async fn upload_not_multipart() {
        let req = Request::post("/upload")
            .header(header::CONTENT_TYPE, "application/json")
            .body(Body::from("{}"))
            .unwrap();
        assert_empty_payload(req).await;
    }

    #[tokio::test]
    async fn upload_without_upload_field() {
        let body = "--X\r\nContent-Disposition: form-data; name=\"other\"; filename=\"a.jpg\"\r\n\r\nabc\r\n--X--\r\n";
        let req = Request::post("/upload")
            .header(header::CONTENT_TYPE, "multipart/form-data; boundary=X")
            .body(Body::from(body))
            .unwrap();
        assert_empty_payload(req).await;
    }

    #[tokio::test]
    async fn feedback_invalid_json() {
        let req = Request::post("/feedback")
            .body(Body::from("not json"))
            .unwrap();
        assert_empty_payload(req).await;
    }

    #[tokio::test]
    async fn feedback_rejects_unknown_ox() {
        let req = Request::post("/feedback")
            .body(Body::from(
                r#"{"id":"1","ox":"$set","file":"2026-11-23/abcd1234_a.jpg"}"#,
            ))
            .unwrap();
        assert_empty_payload(req).await;
    }

    #[tokio::test]
    async fn feedback_rejects_path_traversal() {
        let req = Request::post("/feedback")
            .body(Body::from(
                r#"{"id":"1","ox":"like","file":"../../etc/passwd"}"#,
            ))
            .unwrap();
        assert_empty_payload(req).await;
    }

    #[tokio::test]
    async fn feedback_too_large() {
        let req = Request::post("/feedback")
            .body(Body::from(vec![b' '; 3 << 20]))
            .unwrap();
        assert_empty_payload(req).await;
    }
}
