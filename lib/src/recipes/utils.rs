use std::path::Path;

pub fn file_path_completion(cwd: &Path, partial_name: &str) -> Vec<String> {
    let prefix = if cwd.join(partial_name).is_dir() {
        if partial_name.is_empty() || partial_name.ends_with('/') {
            partial_name.into()
        } else {
            format!("{}/", partial_name)
        }
    } else if let Some(last_slash) = partial_name.rfind('/') {
        partial_name[..last_slash + 1].into()
    } else {
        "".into()
    };

    let cwd = cwd.join(&prefix);
    if !cwd.exists() {
        return vec![];
    }

    match cwd.read_dir() {
        Ok(dir) => dir
            .filter_map(Result::ok)
            .map(|entry| {
                format!(
                    "{}{}",
                    prefix,
                    entry.file_name().into_string().unwrap_or_default()
                )
            })
            .collect(),
        Err(_) => vec![],
    }
}
