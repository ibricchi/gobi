mod toml;
use toml::*;

mod toml_format;
use toml_format::*;

use enum_dispatch::enum_dispatch;
use serde::Deserialize;
use std::{collections::HashMap, path::Path};

use crate::{GobiError, GobiResult};

pub enum EntryType {
    String,
    Integer,
    Float,
    Boolean,
    Array,
    Table,
    Unknown,
}

#[derive(Clone, Debug)]
pub enum EntryIndex {
    Index(usize),
    Key(String),
}

impl<'a> Into<EntryIndex> for usize {
    fn into(self) -> EntryIndex {
        EntryIndex::Index(self)
    }
}
impl Into<EntryIndex> for &str {
    fn into(self) -> EntryIndex {
        EntryIndex::Key(self.into())
    }
}
impl Into<EntryIndex> for String {
    fn into(self) -> EntryIndex {
        EntryIndex::Key(self)
    }
}

pub enum EntryValue {
    Entry(GobiFileEntry),
    String(String),
    Integer(i64),
    Float(f64),
    Boolean(bool),
    Array(Vec<EntryValue>),
    Table(HashMap<String, EntryValue>),
    None,
}

impl From<GobiFileEntry> for EntryValue {
    fn from(value: GobiFileEntry) -> Self {
        EntryValue::Entry(value)
    }
}
impl From<String> for EntryValue {
    fn from(value: String) -> Self {
        EntryValue::String(value)
    }
}
impl From<i64> for EntryValue {
    fn from(value: i64) -> Self {
        EntryValue::Integer(value)
    }
}
impl From<f64> for EntryValue {
    fn from(value: f64) -> Self {
        EntryValue::Float(value)
    }
}
impl From<bool> for EntryValue {
    fn from(value: bool) -> Self {
        EntryValue::Boolean(value)
    }
}
impl From<Vec<EntryValue>> for EntryValue {
    fn from(value: Vec<EntryValue>) -> Self {
        EntryValue::Array(value)
    }
}
impl From<HashMap<String, EntryValue>> for EntryValue {
    fn from(value: HashMap<String, EntryValue>) -> Self {
        EntryValue::Table(value)
    }
}

#[enum_dispatch]
pub trait GobiFileEntryTrait: Sized + Into<GobiFileEntry> {
    fn deserialize<'de, T>(&self) -> GobiResult<T>
    where
        T: Deserialize<'de>;

    fn get_type(&self) -> EntryType;
    fn is_string(&self) -> bool {
        matches!(self.get_type(), EntryType::String)
    }
    fn get_string(&self) -> Option<&str>;
    fn is_integer(&self) -> bool {
        matches!(self.get_type(), EntryType::Integer)
    }
    fn get_integer(&self) -> Option<i64>;
    fn is_float(&self) -> bool {
        matches!(self.get_type(), EntryType::Float)
    }
    fn get_float(&self) -> Option<f64>;
    fn is_boolean(&self) -> bool {
        matches!(self.get_type(), EntryType::Boolean)
    }
    fn get_boolean(&self) -> Option<bool>;
    fn is_array(&self) -> bool {
        matches!(self.get_type(), EntryType::Array)
    }
    fn get_array(&self) -> Option<Vec<GobiFileEntry>> {
        if self.is_array() {
            Some(
                (0..self.len().unwrap())
                    .map(|i| self.get(i).unwrap())
                    .collect(),
            )
        } else {
            None
        }
    }
    fn len(&self) -> Option<usize>;

    fn is_table(&self) -> bool {
        matches!(self.get_type(), EntryType::Table)
    }
    fn get_table(&self) -> Option<HashMap<String, GobiFileEntry>>;
    fn contains(&self, key: &str) -> Option<bool>;

    fn get<I>(&self, idx: I) -> Option<GobiFileEntry>
    where
        I: Into<EntryIndex>,
    {
        match idx.into() {
            EntryIndex::Index(idx) => self.get_array().map_or(None, |mut arr| {
                if idx < arr.len() {
                    Some(arr.swap_remove(idx))
                } else {
                    None
                }
            }),
            EntryIndex::Key(key) => self.get_table().map_or(None, |mut tab| tab.remove(&key)),
        }
    }
    fn get_nested<I>(&self, idxs: &[I]) -> Option<GobiFileEntry>
    where
        I: Into<EntryIndex> + Clone,
    {
        let (first_idx, remaning_idxs) = match idxs.split_first() {
            Some(x) => x,
            None => return None,
        };
        let first_val = self.get(first_idx.clone());
        remaning_idxs
            .into_iter()
            .fold(first_val, move |acc, idx| match acc {
                Some(data) => data.get(idx.clone()),
                None => None,
            })
    }

    fn is_unknown(&self) -> bool {
        matches!(self.get_type(), EntryType::Unknown)
    }
}

#[enum_dispatch(GobiFileEntryTrait)]
pub enum GobiFileEntry {
    Toml(TomlEntry),
    TomlFormat(TomlFormatEntry),
}

#[enum_dispatch]
pub trait GobiFileTrait {
    fn path(&self) -> &Path;

    fn set<I, V>(&mut self, entry: &GobiFileEntry, idx: I, val: V) -> GobiResult<()>
    where
        I: Into<EntryIndex>,
        V: Into<EntryValue>;

    fn drop<I>(&mut self, entry: &GobiFileEntry, idx: I) -> GobiResult<()>
    where
        I: Into<EntryIndex>,
    {
        self.set(entry, idx, EntryValue::None)
    }

    fn push<V>(&mut self, entry: &GobiFileEntry, val: V) -> GobiResult<()>
    where
        V: Into<EntryValue>,
    {
        match entry.len() {
            Some(len) => self.set(entry, len, val),
            _ => Err(GobiError {
                code: 1,
                msg: "Called push on a non-array type".into(),
            }),
        }
    }

    fn pop(&mut self, entry: &GobiFileEntry) -> GobiResult<Option<GobiFileEntry>> {
        match entry.len() {
            Some(0) => Err(GobiError {
                code: 1,
                msg: "Called pop on an empty array".into(),
            }),
            Some(len) => {
                let val = entry.get(len - 1);
                self.set(entry, len - 1, EntryValue::None)?;
                Ok(val)
            }
            _ => Err(GobiError {
                code: 1,
                msg: "Called pop on a non-array type".into(),
            }),
        }
    }

    fn get_data(&self) -> GobiFileEntry;

    fn save(&self) -> GobiResult<()>;
}

#[enum_dispatch(GobiFileTrait)]
pub enum GobiFile {
    Toml(TomlFile),
    TomlFormat(TomlFormatFile),
}

impl GobiFile {
    pub fn from_path(path: &Path) -> GobiResult<GobiFile> {
        TomlFile::from_path(path).map(|f| f.into())
    }

    pub fn from_path_format(path: &Path) -> GobiResult<GobiFile> {
        TomlFormatFile::from_path(path).map(|f| f.into())
    }
}
