//! Port of `api_go/aws/rekognition.go`.

use anyhow::{Result, anyhow};
use aws_sdk_rekognition::Client;
use aws_sdk_rekognition::error::{DisplayErrorContext, ProvideErrorMetadata, SdkError};
use aws_sdk_rekognition::operation::RequestId;
use aws_sdk_rekognition::operation::search_faces_by_image::SearchFacesByImageError;
use aws_sdk_rekognition::primitives::Blob;
use aws_sdk_rekognition::types::Image;

/// Re-indexed collection (Go master "Upgrade v7"); ExternalImageId is `<actress id>_<suffix>`.
pub const COLLECTION_ID: &str = "rankingcollection_v7";
pub const REGION: &str = "us-east-1";

/// Request-side threshold (same value the Go code sends to Rekognition).
const FACE_MATCH_THRESHOLD: f32 = 0.2;
const MAX_FACES: i32 = 20;
/// Local cut-off applied to the returned matches.
const MIN_SIMILARITY: f32 = 20.0;

#[derive(Debug, Clone, PartialEq)]
pub struct Face {
    pub id: String,
    pub similarity: f32,
}

/// Builds the Rekognition client once at startup (Go created a new session per call).
pub async fn new_client() -> Client {
    let config = aws_config::from_env()
        .region(aws_config::Region::new(REGION))
        .load()
        .await;
    Client::new(&config)
}

#[derive(Debug, PartialEq)]
pub enum Search {
    /// Rekognition found no face in the uploaded image (a normal user-side outcome).
    NoFace,
    /// Faces found, but nothing usable in the collection (Go returned `nil, nil`).
    NoMatch,
    Matches(Vec<Face>),
}

pub async fn search_faces_by_image(client: &Client, img_bytes: Vec<u8>) -> Result<Search> {
    let result = client
        .search_faces_by_image()
        .collection_id(COLLECTION_ID)
        .image(Image::builder().bytes(Blob::new(img_bytes)).build())
        .face_match_threshold(FACE_MATCH_THRESHOLD)
        .max_faces(MAX_FACES)
        .send()
        .await;
    let resp = match result {
        Ok(resp) => resp,
        Err(err) if err.as_service_error().is_some_and(is_no_face) => return Ok(Search::NoFace),
        Err(err) => return Err(sdk_error("SearchFacesByImage", err)),
    };

    tracing::debug!(
        matches = resp.face_matches().len(),
        request_id = resp.request_id().unwrap_or("-"),
        "SearchFacesByImage"
    );

    let matches = resp
        .face_matches()
        .iter()
        .map(|m| {
            let external_id = m
                .face()
                .and_then(|f| f.external_image_id())
                .ok_or_else(|| anyhow!("face match without ExternalImageId"))?;
            let id = actress_id(external_id);
            let similarity = m
                .similarity()
                .ok_or_else(|| anyhow!("face match without Similarity"))?;
            Ok(Face {
                id: id.to_string(),
                similarity,
            })
        })
        .collect::<Result<Vec<_>>>()?;

    Ok(filter_matches(matches).map_or(Search::NoMatch, Search::Matches))
}

/// `InvalidParameterException: There are no faces in the image. Should be at least 1.`
fn is_no_face(err: &SearchFacesByImageError) -> bool {
    let SearchFacesByImageError::InvalidParameterException(e) = err else {
        return false;
    };
    // The exception's own `message` field, falling back to the generic error metadata.
    e.message()
        .or_else(|| e.meta().message())
        .is_some_and(|m| m.to_ascii_lowercase().contains("no faces"))
}

/// One-line error: `<op> failed: <code>: <message>` for AWS service errors
/// (the SDK's own Display repeats the message), full context for transport errors.
fn sdk_error<E, R>(op: &str, err: SdkError<E, R>) -> anyhow::Error
where
    E: ProvideErrorMetadata + std::error::Error + 'static,
    R: std::fmt::Debug,
{
    match err.as_service_error() {
        Some(e) => anyhow!(
            "{op} failed: {}: {}",
            e.code().unwrap_or("Unknown"),
            e.message().unwrap_or("")
        ),
        None => anyhow!("{op} failed: {}", DisplayErrorContext(&err)),
    }
}

/// `<actress id>_<suffix>` → `<actress id>` (Go: `strings.SplitN(id, "_", 2)[0]`).
/// An id without `_` is returned unchanged.
fn actress_id(external_image_id: &str) -> &str {
    external_image_id
        .split_once('_')
        .map_or(external_image_id, |(id, _)| id)
}

/// Same selection rules as the Go loop:
/// - no matches, or the first (best) match below 20 → `None`
/// - otherwise keep the first match, then every later match with a new id and similarity >= 20
pub fn filter_matches(matches: Vec<Face>) -> Option<Vec<Face>> {
    let mut iter = matches.into_iter();
    let Some(first) = iter.next() else {
        tracing::debug!("no match for face");
        return None;
    };
    if first.similarity < MIN_SIMILARITY {
        tracing::debug!(similarity = first.similarity, "best match below 20");
        return None;
    }

    let mut faces = vec![first];
    for face in iter {
        if face.similarity >= MIN_SIMILARITY && !faces.iter().any(|f| f.id == face.id) {
            faces.push(face);
        }
    }
    Some(faces)
}

/// Not called anymore: Go master ("Upgrade v7") disabled indexing feedback images.
/// Kept for parity with the Go code.
#[allow(dead_code)]
pub async fn insert_index_face_by_image(
    client: &Client,
    id: &str,
    img_bytes: Vec<u8>,
) -> Result<()> {
    let resp = client
        .index_faces()
        .collection_id(COLLECTION_ID)
        .image(Image::builder().bytes(Blob::new(img_bytes)).build())
        .external_image_id(id)
        .send()
        .await
        .map_err(|err| sdk_error("IndexFaces", err))?;

    tracing::debug!(
        faces = resp.face_records().len(),
        request_id = resp.request_id().unwrap_or("-"),
        "IndexFaces"
    );
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn f(id: &str, similarity: f32) -> Face {
        Face {
            id: id.into(),
            similarity,
        }
    }

    #[test]
    fn empty_is_none() {
        assert_eq!(filter_matches(vec![]), None);
    }

    #[test]
    fn first_below_threshold_is_none() {
        assert_eq!(filter_matches(vec![f("a", 19.9), f("b", 90.0)]), None);
    }

    #[test]
    fn dedupes_and_filters_low_similarity() {
        let got = filter_matches(vec![f("a", 90.0), f("a", 80.0), f("b", 10.0), f("c", 20.0)]);
        assert_eq!(got, Some(vec![f("a", 90.0), f("c", 20.0)]));
    }

    #[test]
    fn detects_no_face_error() {
        use aws_sdk_rekognition::types::error::{
            InvalidImageFormatException, InvalidParameterException,
        };

        let no_face = SearchFacesByImageError::InvalidParameterException(
            InvalidParameterException::builder()
                .message("There are no faces in the image. Should be at least 1.")
                .build(),
        );
        assert!(is_no_face(&no_face));

        let other_param = SearchFacesByImageError::InvalidParameterException(
            InvalidParameterException::builder()
                .message("MaxFaces out of range")
                .build(),
        );
        assert!(!is_no_face(&other_param));

        let bad_format = SearchFacesByImageError::InvalidImageFormatException(
            InvalidImageFormatException::builder()
                .message("no faces")
                .build(),
        );
        assert!(!is_no_face(&bad_format));
    }

    #[test]
    fn actress_id_strips_suffix() {
        assert_eq!(actress_id("1016186_abc"), "1016186");
        assert_eq!(actress_id("1016186_a_b"), "1016186");
        assert_eq!(actress_id("1016186"), "1016186");
    }

    #[test]
    fn dedupes_by_actress_id_not_full_external_id() {
        // Go master compared the full ExternalImageId against stripped ids, so the same
        // actress could appear twice. We dedupe on the stripped id.
        let ids = ["1016186_x", "1016186_y", "1041730_z"];
        let got = filter_matches(
            ids.iter()
                .zip([94.0, 93.0, 92.0])
                .map(|(e, s)| f(actress_id(e), s))
                .collect(),
        );
        assert_eq!(got, Some(vec![f("1016186", 94.0), f("1041730", 92.0)]));
    }
}
