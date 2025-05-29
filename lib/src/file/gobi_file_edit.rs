use std::{
    fs::File,
    io::{Read, Write},
    path::{Path, PathBuf},
};

use crate::{GobiError, GobiResult};

#[derive(Debug)]
pub struct GobiFileEdit {
    path: PathBuf,
    data: toml_edit::DocumentMut,
}

impl GobiFileEdit {
    pub fn from_path<P: Into<PathBuf>>(path: P) -> GobiResult<GobiFileEdit> {
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
        let data = match contents.parse::<toml_edit::DocumentMut>() {
            Err(e) => {
                return Err(GobiError {
                    code: 1,
                    msg: e.to_string(),
                });
            }
            Ok(data) => data,
        };

        Ok(GobiFileEdit { path, data })
    }

    pub fn as_item(&self) -> &toml_edit::Item {
        self.data.as_item()
    }

    pub fn as_item_mut(&mut self) -> &mut toml_edit::Item {
        self.data.as_item_mut()
    }

    pub fn path(&self) -> &Path {
        &self.path
    }

    pub fn save(&self) -> GobiResult<()> {
        let data = self.data.to_string();
        let mut file = match File::create(&self.path) {
            Err(e) => {
                return Err(GobiError {
                    code: 1,
                    msg: e.to_string(),
                });
            }
            Ok(file) => file,
        };

        match file.write(data.as_bytes()) {
            Err(e) => {
                return Err(GobiError {
                    code: 1,
                    msg: e.to_string(),
                });
            }
            Ok(..) => Ok(()),
        }
    }
}
