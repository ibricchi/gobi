use serde::Deserialize;
use std::{
    collections::HashMap,
    fs::File,
    io::{Read, Write},
    path::{Path, PathBuf},
    str::FromStr,
};

use crate::{
    file::{EntryIndex, EntryType, EntryValue, GobiFileEntryTrait, GobiFileTrait},
    GobiError, GobiResult, GobiResultIterator,
};

use super::GobiFileEntry;

#[derive(Debug)]
pub struct TomlFormatEntry {
    data: toml_edit::Item,
    path: Vec<EntryIndex>,
}

impl TryFrom<EntryValue> for toml_edit::Item {
    type Error = GobiError;

    fn try_from(value: EntryValue) -> Result<Self, Self::Error> {
        match value {
            EntryValue::Entry(GobiFileEntry::TomlFormat(val)) => Ok(val.data),
            EntryValue::Entry(_) => Err(GobiError {
                code: 1,
                msg: "Tried converting non TomlFormat value into a toml_edit::Value".into(),
            }),
            EntryValue::String(val) => Ok(toml_edit::Item::Value(toml_edit::Value::String(
                toml_edit::Formatted::<String>::new(val),
            ))),
            EntryValue::Integer(val) => Ok(toml_edit::Item::Value(toml_edit::Value::Integer(
                toml_edit::Formatted::<i64>::new(val),
            ))),
            EntryValue::Float(val) => Ok(toml_edit::Item::Value(toml_edit::Value::Float(
                toml_edit::Formatted::<f64>::new(val),
            ))),
            EntryValue::Boolean(val) => Ok(toml_edit::Item::Value(toml_edit::Value::Boolean(
                toml_edit::Formatted::<bool>::new(val),
            ))),
            EntryValue::Array(val) => Ok(toml_edit::Item::Value(toml_edit::Value::Array(
                GobiResultIterator::from(val.into_iter().map(|val| match val.try_into() {
                    Ok(toml_edit::Item::Value(val)) => Ok(val),
                    Err(e) => Err(e),
                    _ => todo!(),
                }))
                .try_collect()?,
            ))),
            EntryValue::Table(val) => Ok(toml_edit::Item::Table(
                GobiResultIterator::from(val.into_iter().map(|(key, val)| {
                    match toml_edit::Item::try_from(val) {
                        Ok(val) => Ok((key, val)),
                        Err(e) => Err(e),
                    }
                }))
                .try_collect()?,
            )),
            EntryValue::None => Err(GobiError {
                code: 1,
                msg: "Cannot convert EntryValue::None type into toml_edit::Value".into(),
            }),
        }
    }
}

impl TryFrom<&TomlFormatEntry> for toml::Value {
    type Error = GobiError;

    fn try_from(value: &TomlFormatEntry) -> Result<Self, Self::Error> {
        match &value.data {
            toml_edit::Item::Value(toml_edit::Value::String(val)) => {
                Ok(toml::Value::String(val.clone().into_value()))
            }
            toml_edit::Item::Value(toml_edit::Value::Integer(val)) => {
                Ok(toml::Value::Integer(val.clone().into_value()))
            }
            toml_edit::Item::Value(toml_edit::Value::Float(val)) => {
                Ok(toml::Value::Float(val.clone().into_value()))
            }
            toml_edit::Item::Value(toml_edit::Value::Boolean(val)) => {
                Ok(toml::Value::Boolean(val.clone().into_value()))
            }
            toml_edit::Item::Value(toml_edit::Value::Datetime(val)) => {
                Ok(toml::Value::Datetime(val.clone().into_value()))
            }
            toml_edit::Item::Value(toml_edit::Value::Array(arr)) => Ok(toml::Value::Array(
                GobiResultIterator::from(arr.into_iter().map(|data| {
                    TryInto::<toml::Value>::try_into(&TomlFormatEntry {
                        data: data.into(),
                        path: vec![],
                    })
                }))
                .try_collect()?,
            )),
            toml_edit::Item::Value(toml_edit::Value::InlineTable(tab)) => Ok(toml::Value::Table(
                GobiResultIterator::from(tab.into_iter().map(|(key, val)| {
                    TryInto::<toml::Value>::try_into(&TomlFormatEntry {
                        data: toml_edit::Item::Value(val.clone()),
                        path: vec![],
                    })
                    .map(|val| (key.into(), val))
                }))
                .try_collect()?,
            )),
            toml_edit::Item::Table(tab) => Ok(toml::Value::Table(
                GobiResultIterator::from(tab.into_iter().map(|(key, val)| {
                    TryInto::<toml::Value>::try_into(&TomlFormatEntry {
                        data: val.clone(),
                        path: vec![],
                    })
                    .map(|val| (key.into(), val))
                }))
                .try_collect()?,
            )),
            toml_edit::Item::ArrayOfTables(arr) => Ok(toml::Value::Array(
                GobiResultIterator::from(arr.into_iter().map(|data| {
                    TryInto::<toml::Value>::try_into(&TomlFormatEntry {
                        data: toml_edit::Item::Table(data.clone()),
                        path: vec![],
                    })
                }))
                .try_collect()?,
            )),
            toml_edit::Item::None => Err(GobiError {
                code: 1,
                msg: "Cannot convert toml_edit::Item::None type into toml::Value".into(),
            }),
        }
    }
}

impl GobiFileEntryTrait for TomlFormatEntry {
    fn deserialize<'de, T>(&self) -> GobiResult<T>
    where
        T: Deserialize<'de>,
    {
        let val: toml::Value = TryFrom::<&TomlFormatEntry>::try_from(self)?;
        match T::deserialize(val) {
            Ok(t) => Ok(t),
            Err(e) => Err(GobiError {
                code: 1,
                msg: format!("Failed to deserialize '{}'", e),
            }),
        }
    }

    fn get_type(&self) -> EntryType {
        match self.data {
            toml_edit::Item::Value(toml_edit::Value::String(..)) => EntryType::String,
            toml_edit::Item::Value(toml_edit::Value::Integer(..)) => EntryType::Integer,
            toml_edit::Item::Value(toml_edit::Value::Float(..)) => EntryType::Float,
            toml_edit::Item::Value(toml_edit::Value::Boolean(..)) => EntryType::Boolean,
            toml_edit::Item::Value(toml_edit::Value::Array(..)) => EntryType::Array,
            toml_edit::Item::Table(..) => EntryType::Table,
            _ => EntryType::Unknown,
        }
    }

    fn get_string(&self) -> Option<&str> {
        self.data.as_str()
    }

    fn get_integer(&self) -> Option<i64> {
        self.data.as_integer()
    }

    fn get_float(&self) -> Option<f64> {
        self.data.as_float()
    }

    fn get_boolean(&self) -> Option<bool> {
        self.data.as_bool()
    }

    fn len(&self) -> Option<usize> {
        self.data.as_array().map(|arr| arr.len())
    }

    fn get_table(&self) -> Option<HashMap<String, GobiFileEntry>> {
        match self.data.as_table() {
            Some(tab) => Some(
                tab.into_iter()
                    .map(|(key, data)| {
                        let mut path = self.path.clone();
                        path.push(EntryIndex::Key(key.into()));
                        (
                            key.into(),
                            Self {
                                data: data.clone(),
                                path,
                            }
                            .into(),
                        )
                    })
                    .collect(),
            ),
            None => None,
        }
    }

    fn contains(&self, key: &str) -> Option<bool> {
        self.data.as_table().map(|tab| tab.contains_key(key))
    }
}

pub struct TomlFormatFile {
    path: PathBuf,
    data: toml_edit::DocumentMut,
}

impl TomlFormatFile {
    pub fn from_path<P: Into<PathBuf>>(path: P) -> GobiResult<TomlFormatFile> {
        // open the file to read it's contents
        let path = path.into();
        let mut file = match File::open(&path) {
            Err(e) => {
                return Err(GobiError {
                    code: 1,
                    msg: e.to_string(),
                });
            }
            Ok(file) => file,
        };

        // read the contents of the file
        let mut contents = String::new();
        match file.read_to_string(&mut contents) {
            Err(e) => {
                return Err(GobiError {
                    code: 1,
                    msg: e.to_string(),
                });
            }
            Ok(_) => (),
        }

        // parse the contents of the file
        let data = match toml_edit::DocumentMut::from_str(&contents) {
            Err(e) => {
                return Err(GobiError {
                    code: 1,
                    msg: e.to_string(),
                });
            }
            Ok(data) => data,
        };

        Ok(TomlFormatFile { path, data })
    }

    fn get_data_mut(&mut self) -> &mut toml_edit::Item {
        self.data.as_item_mut()
    }
}

impl GobiFileTrait for TomlFormatFile {
    fn path(&self) -> &Path {
        &self.path
    }

    fn get_data(&self) -> GobiFileEntry {
        TomlFormatEntry {
            data: self.data.as_item().clone(),
            path: vec![],
        }
        .into()
    }

    fn set<I, V>(&mut self, entry: &GobiFileEntry, idx: I, val: V) -> GobiResult<()>
    where
        I: Into<EntryIndex>,
        V: Into<EntryValue>,
    {
        let entry =
            match entry {
                GobiFileEntry::TomlFormat(entry) => entry,
                _ => return Err(GobiError {
                    code: 1,
                    msg:
                        "Tried setting value of entry in TomlFormatFile with a non TomlFormatEntry"
                            .into(),
                }),
            };
        let top_value = self.get_data_mut();
        let container = if entry.path.len() > 0 {
            let first_entry = match &entry.path[0] {
                EntryIndex::Index(idx) => top_value.get_mut(idx),
                EntryIndex::Key(key) => top_value.get_mut(key),
            };
            entry.path[1..]
                .into_iter()
                .fold(first_entry.unwrap(), move |val, idx| {
                    match idx {
                        EntryIndex::Index(idx) => val.get_mut(idx),
                        EntryIndex::Key(key) => val.get_mut(key),
                    }
                    .unwrap()
                })
        } else {
            top_value
        };

        match idx.into() {
            EntryIndex::Index(idx) => match container.as_array_mut() {
                Some(arr) => {
                    if idx < arr.len() {
                        match val.into() {
                            EntryValue::None => {
                                arr.remove(idx);
                            }
                            entry => {
                                *arr.get_mut(idx).unwrap() = match entry.try_into()? {
                                    toml_edit::Item::Value(v) => v,
                                    _ => todo!(),
                                };
                            }
                        }
                        Ok(())
                    } else {
                        Err(GobiError {
                            code: 1,
                            msg: "Tried setting out of bounds index into array".into(),
                        })
                    }
                }
                None => Err(GobiError {
                    code: 1,
                    msg: "Tried setting an integer index on a non-array type".into(),
                }),
            },
            EntryIndex::Key(key) => match container.as_table_mut() {
                Some(tab) => {
                    match val.into() {
                        EntryValue::None => {
                            tab.remove(&key);
                        }
                        entry => tab[&key] = entry.try_into()?,
                    }
                    Ok(())
                }
                None => Err(GobiError {
                    code: 1,
                    msg: "Tried setting a string key on a non-table type".into(),
                }),
            },
        }
    }

    fn save(&self) -> GobiResult<()> {
        let mut file = match File::create(&self.path) {
            Ok(f) => f,
            Err(..) => {
                return Err(GobiError {
                    code: 1,
                    msg: format!("Failed to open file '{}'", self.path.to_str().unwrap()),
                })
            }
        };

        match file.write(self.data.to_string().as_bytes()) {
            Ok(..) => Ok(()),
            Err(e) => Err(GobiError {
                code: 1,
                msg: format!(
                    "Could not write to file '{}': {}",
                    self.path.to_str().unwrap(),
                    e.to_string()
                ),
            }),
        }
    }
}
