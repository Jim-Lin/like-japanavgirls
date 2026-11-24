//! Port of `api_go/db/mongodb.go`.

use std::collections::HashMap;
use std::path::Path;

use anyhow::{Context, Result, anyhow};
use chrono::{Datelike, Days, Local, NaiveDate};
use mongodb::bson::{Document, doc};
use mongodb::options::{ClientOptions, Credential, ServerAddress};
use mongodb::{Client, Database};

pub const HOST: &str = "localhost";
pub const PORT: u16 = 27017;
pub const DATABASE: &str = "dark";
const PROPERTIES_FILE: &str = "mongodb.properties";

#[allow(dead_code)]
#[derive(Debug, Clone, PartialEq)]
pub struct Rank {
    pub id: String,
    pub count: i64,
}

/// Equivalent of Go's `init()`: reads `./mongodb.properties` (username / password)
/// and connects to `localhost:27017/dark`, authenticating against `dark`.
pub async fn connect() -> Result<Database> {
    let path = std::env::current_dir()?.join(PROPERTIES_FILE);
    let props = load_properties(&path)?;
    let get = |key: &str| {
        props
            .get(key)
            .cloned()
            .ok_or_else(|| anyhow!("{key} not found in {}", path.display()))
    };

    let mut options = ClientOptions::default();
    options.hosts = vec![ServerAddress::Tcp {
        host: HOST.into(),
        port: Some(PORT),
    }];
    options.credential = Some(
        Credential::builder()
            .username(get("username")?)
            .password(get("password")?)
            .source(DATABASE.to_string())
            .build(),
    );

    let client = Client::with_options(options)?;
    let db = client.database(DATABASE);
    // mgo.DialWithInfo fails immediately when the server/auth is bad; do the same.
    db.run_command(doc! { "ping": 1 })
        .await
        .context("failed to connect to MongoDB")?;
    Ok(db)
}

/// Minimal Java-style `.properties` reader (`key=value` / `key: value`, `#`/`!` comments),
/// which is all `magiconair/properties` was used for.
fn load_properties(path: &Path) -> Result<HashMap<String, String>> {
    let text = std::fs::read_to_string(path)
        .with_context(|| format!("failed to read {}", path.display()))?;
    Ok(parse_properties(&text))
}

fn parse_properties(text: &str) -> HashMap<String, String> {
    text.lines()
        .map(str::trim)
        .filter(|l| !l.is_empty() && !l.starts_with('#') && !l.starts_with('!'))
        .filter_map(|l| {
            let idx = l.find(['=', ':'])?;
            Some((l[..idx].trim().to_string(), l[idx + 1..].trim().to_string()))
        })
        .collect()
}

/// Returns `{name, img}` of the actress, or `None` when not found
/// (Go panicked with `not found`, which ended in the empty payload).
pub async fn find_one_actress(db: &Database, id: &str) -> Result<Option<HashMap<String, String>>> {
    let found = db
        .collection::<Document>("actress")
        .find_one(doc! { "id": id })
        .projection(doc! { "name": 1, "img": 1, "_id": 0 })
        .await?;

    Ok(found.map(|d| {
        d.into_iter()
            .filter_map(|(k, v)| v.as_str().map(|s| (k, s.to_string())))
            .collect()
    }))
}

/// Allowed values of the feedback `ox` field. It is used as a Mongo field name in `$push`,
/// so it must never come straight from the client (Go pushed to any client-supplied key).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Vote {
    Like,
    Unlike,
}

impl Vote {
    pub fn parse(ox: &str) -> Result<Self> {
        match ox {
            "like" => Ok(Vote::Like),
            "unlike" => Ok(Vote::Unlike),
            other => Err(anyhow!("invalid ox: {other:?}")),
        }
    }

    pub fn as_str(self) -> &'static str {
        match self {
            Vote::Like => "like",
            Vote::Unlike => "unlike",
        }
    }
}

pub async fn upsert_one_feedback(db: &Database, id: &str, ox: Vote, image: &str) -> Result<()> {
    db.collection::<Document>("actress")
        .update_one(doc! { "id": id }, feedback_update(ox, image))
        .upsert(true)
        .await?;
    Ok(())
}

fn feedback_update(ox: Vote, image: &str) -> Document {
    doc! { "$inc": { "count": 1 }, "$push": { ox.as_str(): image } }
}

pub async fn upsert_one_week_rank(db: &Database, id: &str) -> Result<()> {
    let now = Local::now().iso_week();
    db.collection::<Document>("rank")
        .update_one(
            doc! { "week": week_key(now.year(), now.week()) },
            doc! { "$push": { "vote": id } },
        )
        .upsert(true)
        .await?;
    Ok(())
}

/// Not used by any handler (same as in Go), kept for parity.
#[allow(dead_code)]
pub async fn aggregate_week_rank(db: &Database) -> Result<Vec<Rank>> {
    use futures_util::TryStreamExt;

    let last_week = last_week_key(Local::now().date_naive());
    let pipeline = vec![
        doc! { "$match": { "week": last_week } },
        doc! { "$unwind": "$vote" },
        doc! { "$group": { "_id": "$vote", "count": { "$sum": 1 } } },
        doc! { "$sort": { "count": -1 } },
        doc! { "$limit": 5 },
    ];

    let docs: Vec<Document> = db
        .collection::<Document>("rank")
        .aggregate(pipeline)
        .await?
        .try_collect()
        .await?;
    docs.into_iter()
        .map(|d| {
            let id = d.get_str("_id")?.to_string();
            let count = match d.get("count") {
                Some(mongodb::bson::Bson::Int32(n)) => *n as i64,
                Some(mongodb::bson::Bson::Int64(n)) => *n,
                other => return Err(anyhow!("unexpected count: {other:?}")),
            };
            Ok(Rank { id, count })
        })
        .collect()
}

/// Key of the ISO week before `today`. Go used `week - 1`, which gave "<year>0" in week 1;
/// going back 7 days lands in the previous ISO week, including across year boundaries.
fn last_week_key(today: NaiveDate) -> String {
    let w = (today - Days::new(7)).iso_week();
    week_key(w.year(), w.week())
}

/// `strconv.Itoa(year) + strconv.Itoa(week)` — no zero padding, e.g. 2026 week 3 → "20263".
fn week_key(year: i32, week: impl std::fmt::Display) -> String {
    format!("{year}{week}")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn week_key_has_no_padding() {
        assert_eq!(week_key(2026, 3u32), "20263");
        assert_eq!(week_key(2026, 48u32), "202648");
    }

    #[test]
    fn iso_week_year_is_used() {
        // 2027-01-01 belongs to ISO week 53 of 2026.
        let w = chrono::NaiveDate::from_ymd_opt(2027, 1, 1)
            .unwrap()
            .iso_week();
        assert_eq!(week_key(w.year(), w.week()), "202653");
    }

    #[test]
    fn feedback_push_key_is_ox_value() {
        let d = feedback_update(Vote::Like, "2026-11-23/a.jpg");
        assert_eq!(
            d.get_document("$push").unwrap().get_str("like").unwrap(),
            "2026-11-23/a.jpg"
        );
    }

    #[test]
    fn feedback_push_key_unlike() {
        let d = feedback_update(Vote::Unlike, "x");
        assert_eq!(
            d.get_document("$push").unwrap().get_str("unlike").unwrap(),
            "x"
        );
    }

    #[test]
    fn vote_only_accepts_whitelist() {
        assert_eq!(Vote::parse("like").unwrap(), Vote::Like);
        assert_eq!(Vote::parse("unlike").unwrap(), Vote::Unlike);
        for bad in ["", "dislike", "Like", "$set", "a.b", "like "] {
            assert!(Vote::parse(bad).is_err(), "{bad:?} should be rejected");
        }
    }

    #[test]
    fn last_week_crosses_year_boundary() {
        let d = |y, m, day| NaiveDate::from_ymd_opt(y, m, day).unwrap();
        // 2027-01-04 is ISO 2027-W01 → previous week is 2026-W53 (Go gave "20270").
        assert_eq!(last_week_key(d(2027, 1, 4)), "202653");
        // 2026-01-05 is ISO 2026-W02 → 2026-W01.
        assert_eq!(last_week_key(d(2026, 1, 5)), "20261");
        // 2026-11-23 is ISO 2026-W48 → 2026-W47.
        assert_eq!(last_week_key(d(2026, 11, 23)), "202647");
    }

    #[test]
    fn parses_properties() {
        let p = parse_properties("# comment\nusername = alice\npassword:p=ss\n\n");
        assert_eq!(p.get("username").map(String::as_str), Some("alice"));
        assert_eq!(p.get("password").map(String::as_str), Some("p=ss"));
    }
}
