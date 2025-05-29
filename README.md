<img src="logo.png" width="200" />

# gobi

Gobi, stylized in lowercase as gobi, is a command line utility to conveniently manage helper scripts for your project.

## Installation

To install just clone the repository, build using cargo

```bash
git clone github.com/ibricchi/gobi
cd gobi
cargo build --release
```

And add `target/release/gobi_cli` and `scripts/gobi` to your path, for tab completions on zsh
also source `scripts/gobi.zsh` in your zshrc

## Usage

gobi is run using the following syntax:

```bash
gobi [projects...] [action] [args...]
```

gobi relies on gobi files to configure the scripts to run. A gobi file is a toml file with the following basic structure:

```toml
[sehll.example]
command = """
    echo "hello world"
"""

[gobi.projects]
project1 = "path/to/project1/gobi.toml"
project2 = "path/to/project2/gobi.toml"
```

### Recipes

Recipes are the heart of gobi, each one reads the gobi file and configures a set of actions for the user to run. The following recipes are included with gobi:

- argparse: create a command line argument passer to set up env variables for a child action
- help: prints a help message for any recipe, or action that supports this feature
- include: include definitions from anohter gobi file
- list: list all action in the current project
- project-manager: helps manage child projects
- sequence: runs a sequence of actions
- shell: generates actions to run shell commands

More information about each can be found by running `gobi help <recipe>`

### Actions

Actions are the commands that gobi runs. When run extra arguments can be passed to the arguments, some actions may use them some may not, this is up to the recipe that generated the action.

## Example

Here is an example gobi file.

```toml
[shell.hello]
command="""
    echo "Hello World!"
"""
```

Save this file and add it as a project by running:

```bash
gobi register example-project path/to/example/gobi.toml
```

Now we can see that the project has been added by running:

```bash
gobi list
```

You should see "example-project" in the list.

Now we can run the hello action by running:

```bash
gobi example-project hello
```

You should see "Hello World!" printed to the terminal.

## Development

TODO!

## Contributing

Pull requests are welcome
