use serde::Deserialize;
use std::{
    collections::HashMap,
    fs::File,
    io::Read,
    path::{Path, PathBuf},
    str::FromStr,
};

use crate::{
    file::{EntryIndex, EntryType, EntryValue, GobiFileEntryTrait, GobiFileTrait},
    GobiError, GobiResult,
};

use super::GobiFileEntry;

#[derive(Debug)]
pub struct TomlEntry {
    data: toml::Value,
    path: Vec<EntryIndex>,
}

impl TryInto<toml::Value> for EntryValue {
    type Error = GobiError;

    fn try_into(self) -> Result<toml::Value, Self::Error> {
        match self {
            EntryValue::String(val) => Ok(toml::Value::String(val.into())),
            EntryValue::Integer(val) => Ok(toml::Value::Integer(val)),
            EntryValue::Float(val) => Ok(toml::Value::Float(val)),
            EntryValue::Boolean(val) => Ok(toml::Value::Boolean(val)),
            EntryValue::Array(val) => {
                let (vals, err): (Vec<toml::Value>, GobiError) =
                    val.into_iter()
                        .fold(
                            (vec![], GobiError::default()),
                            |(mut vals, err), val| match val.try_into() {
                                Ok(val) => {
                                    vals.push(val);
                                    (vals, err)
                                }
                                Err(e) => (vals, err.merge(e)),
                            },
                        );
                if err.code != 0 {
                    Err(err)
                } else {
                    Ok(toml::Value::Array(vals))
                }
            }
            EntryValue::Table(val) => {
                type Map = toml::map::Map<String, toml::Value>;
                let (vals, err): (Map, GobiError) = val.into_iter().fold(
                    (Map::new(), GobiError::default()),
                    |(mut vals, err), (key, val)| match val.try_into() {
                        Ok(val) => {
                            vals[&key] = val;
                            (vals, err)
                        }
                        Err(e) => (vals, err.merge(e)),
                    },
                );
                if err.code != 0 {
                    Err(err)
                } else {
                    Ok(toml::Value::Table(vals))
                }
            }
            EntryValue::None => Err(GobiError {
                code: 1,
                msg: "Cannot convert EntryValue::None type into toml::Value".into(),
            }),
        }
    }
}

impl GobiFileEntryTrait for TomlEntry {
    fn deserialize<'de, T>(&self) -> GobiResult<T>
    where
        T: Deserialize<'de>,
    {
        match T::deserialize(self.data.clone()) {
            Ok(t) => Ok(t),
            Err(e) => Err(GobiError {
                code: 1,
                msg: format!("Failed to deserialize '{}'", e),
            }),
        }
    }

    fn get_type(&self) -> EntryType {
        match self.data {
            toml::Value::String(..) => EntryType::String,
            toml::Value::Integer(..) => EntryType::Integer,
            toml::Value::Float(..) => EntryType::Float,
            toml::Value::Boolean(..) => EntryType::Boolean,
            toml::Value::Array(..) => EntryType::Array,
            toml::Value::Table(..) => EntryType::Table,
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
                            key.clone(),
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

pub struct TomlFile {
    path: PathBuf,
    data: toml::Value,
}

impl TomlFile {
    pub fn from_path<P: Into<PathBuf>>(path: P) -> GobiResult<TomlFile> {
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
        let data = match toml::Value::from_str(&contents) {
            Err(e) => {
                return Err(GobiError {
                    code: 1,
                    msg: e.to_string(),
                });
            }
            Ok(data) => data,
        };

        Ok(TomlFile { path, data })
    }

    fn get_data_mut(&mut self) -> &mut toml::Value {
        &mut self.data
    }
}

impl GobiFileTrait for TomlFile {
    fn path(&self) -> &Path {
        &self.path
    }

    fn get_data(&self) -> GobiFileEntry {
        TomlEntry {
            data: self.data.clone(),
            path: vec![],
        }
        .into()
    }

    fn set<I, V>(&mut self, entry: &GobiFileEntry, idx: I, val: V) -> GobiResult<()>
    where
        I: Into<EntryIndex>,
        V: Into<EntryValue>,
    {
        let entry = match entry {
            GobiFileEntry::Toml(entry) => entry,
            _ => {
                return Err(GobiError {
                    code: 1,
                    msg: "Tried setting value of entry in TomlFile with a non TomlEntry".into(),
                })
            }
        };
        let top_value = self.get_data_mut();
        let first_entry = match &entry.path[0] {
            EntryIndex::Index(idx) => top_value.get_mut(idx),
            EntryIndex::Key(key) => top_value.get_mut(key),
        };
        let container = entry.path[1..]
            .into_iter()
            .fold(first_entry.unwrap(), move |val, idx| {
                match idx {
                    EntryIndex::Index(idx) => val.get_mut(idx),
                    EntryIndex::Key(key) => val.get_mut(key),
                }
                .unwrap()
            });

        match idx.into() {
            EntryIndex::Index(idx) => match container.as_array_mut() {
                Some(arr) => {
                    if idx < arr.len() {
                        match val.into() {
                            EntryValue::None => {
                                arr.remove(idx);
                            }
                            entry => {
                                arr[idx] = entry.try_into()?;
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
}
