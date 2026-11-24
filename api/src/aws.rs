//! Port of `api_go/aws/rekognition.go`.

use anyhow::{Context, Result, anyhow};
use aws_sdk_rekognition::Client;
use aws_sdk_rekognition::operation::RequestId;
use aws_sdk_rekognition::primitives::Blob;
use aws_sdk_rekognition::types::Image;

pub const COLLECTION_ID: &str = "rankingcollection";
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

/// Returns `Ok(None)` when there is no usable match (Go returned `nil, nil`).
pub async fn search_faces_by_image(
    client: &Client,
    img_bytes: Vec<u8>,
) -> Result<Option<Vec<Face>>> {
    let resp = client
        .search_faces_by_image()
        .collection_id(COLLECTION_ID)
        .image(Image::builder().bytes(Blob::new(img_bytes)).build())
        .face_match_threshold(FACE_MATCH_THRESHOLD)
        .max_faces(MAX_FACES)
        .send()
        .await
        .context("SearchFacesByImage failed")?;

    tracing::debug!(
        matches = resp.face_matches().len(),
        request_id = resp.request_id().unwrap_or("-"),
        "SearchFacesByImage"
    );

    let matches = resp
        .face_matches()
        .iter()
        .map(|m| {
            let id = m
                .face()
                .and_then(|f| f.external_image_id())
                .ok_or_else(|| anyhow!("face match without ExternalImageId"))?;
            let similarity = m
                .similarity()
                .ok_or_else(|| anyhow!("face match without Similarity"))?;
            Ok(Face {
                id: id.to_string(),
                similarity,
            })
        })
        .collect::<Result<Vec<_>>>()?;

    Ok(filter_matches(matches))
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
        .context("IndexFaces failed")?;

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
}
