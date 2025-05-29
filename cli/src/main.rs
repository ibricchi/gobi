use std::env;
use std::rc::Rc;

use gobi_lib::recipes::*;

fn main() {
    let user_home = env::var("HOME").unwrap();

    let gobi_core_path =
        env::var("GOBI_CORE_FILE").unwrap_or(format!("{}/.config/gobi/gobi.toml", user_home));

    let mut recipe_manager = Rc::new(RecipeManager::new());
    {
        let mut_recipe_manager = Rc::get_mut(&mut recipe_manager).unwrap();
        gobi::register_recipes(mut_recipe_manager);
        match env::current_exe() {
            Ok(path) => {
                let dir_name = path.parent().unwrap();
                let lib_path = dir_name.join("libgobi_recipes.so");
                if !lib_path.exists() {
                    eprintln!("Could not find libgobi_recipes.so");
                    std::process::exit(1);
                }
                mut_recipe_manager.register_recipes_from_so(&lib_path);
            }
            Err(e) => {
                eprintln!("Error loading default recipes: {}", e);
                std::process::exit(1);
            }
        }
    }

    let program_name = env::args().next().unwrap_or_else(|| "gobi_cli".to_string());
    if env::args().len() < 2 {
        eprintln!("Usage: {} <mode> [args]", program_name);
        std::process::exit(1);
    }
    let mode = env::args().nth(1).unwrap();
    let args = env::args().skip(2).collect::<Vec<String>>();

    let gobi_action = gobi::GobiAction::new("", &gobi_core_path, &recipe_manager);

    match mode.as_str() {
        "run" => {
            if let Err(e) = gobi_action.run(&vec![], args) {
                eprintln!("Error: {}", e.msg);
                std::process::exit(e.code);
            }
        }
        "completion" => {
            match gobi_action.completion(&vec![], args) {
                Err(e) =>  {
                    eprintln!("Error: {}", e.msg);
                    std::process::exit(e.code);
                }
                Ok(completions) => {
                    for completion in completions {
                        println!("{}", completion);
                    }
                }
            }
        }
        _ => {
            eprintln!("Unknown mode: {}", mode);
            eprintln!("Usage: {} <mode> [args]", program_name);
            std::process::exit(1);
        }
    }
}
