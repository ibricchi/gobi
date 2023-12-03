<img src="logo.svg" width="200" />

# gobi

Gobi, stylized in lowercase as gobi, is a command line utility to conveniently manage helper scripts for your project.

## Installation

To install just clone the repository and make a symlink to the `gobi` script in your path.

```bash
git clone github.com/ibricchi/gobi ~/.gobi --recurse-submodules
ln -s ~/.gobi/gobi ~/bin/gobi
```

## Usage

gobi is run using the following syntax:

```bash
gobi [projects...] [action] [args...]
```

gobi relies on gobi files to configure the scripts to run. A gobi file is a toml file with the following basic structure:

```toml
[gobi]
recipes = ["recipe1", "recipe2"]
child-recipes = ["recipe3", "recipe4"]

[gobi.projects]
project1 = "path/to/project1/gobi.toml"
project2 = "path/to/project2/gobi.toml"
```

The recipe section loads a list of plugins to gobi that read the gobi file and produce a list of actions for the user to run. A set of default plugins is included with gobi, but users can also write their own plugins and store them in $GOBI_CUSTOM_RECIPES (must be defined by user). 

The projects section lists children gobi files, when running gobi specifying a project will load it's gobi file, parse it, and run gobi as if it were the main gobi file. This allows for a hierarchical structure of gobi files to be used to manage projects.

Child recipes are recipes that will be automatically set for any child projects. Here we can put any core recipes, such as 'help' and 'list' so we don't have to repeat ourselves in every project.

The core gobi file is loaded from $GOBI_CORE_FILE, if this is not defined it defaults to the gobi.toml file included in the gobi repository clone.

### Recipes

Recipes are the heart of gobi, each one reads the gobi file and configures a set of actions for the user to run. The following recipes are included with gobi:

- help: prints a help message for any recipe, or action that supports this feature
- list: list all action in the current project
- shell: generates actions to run shell commands
- project-manager: helps manage child projects
- sequence: runs a sequence of actions

More information about each can be found by running `gobi help recipe <recipe>`

### Actions

Actions are the commands that gobi runs. When run extra arguments can be passed to the arguments, some actions may use them some may not, this is up to the recipe that generated the action.

## Example

Here is an example gobi file.

```toml
[gobi.recipes]
recipes = ["help", "list", "shell"]

[shell.hello]
command="""
    echo "Hello World!"
"""
```

Save this file and add it as a project by running:

```bash
gobi register example-project path/to/example/gobi.toml
```
Note this requires the "project-manager" manager recipe to be loaded in the core gobi file.

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

If you want to extend gobi with your own recipes, you can do so by adding a python file to a directory specified by setting the $GOBI_CUSTOM_RECIPES environment variable. 

To get started you can copy the template recipe file from the recipes directory in the gobi repository.

The recipe class must have the following methods:
- `__init__(self)`: the constructor, should just set the name of the recipe
- `get_actions(self, gobi_file: GobiFile)`: this method should return a list of actions to be run by gobi, the gobi_file argument is a dictionary containing the parsed gobi file

Optionally the recipe class can also have a `help(self) -> str` method, which should return a string containing a help message for the recipe.

The recipe can have multiple action classes, and can return as many instances of each as it wants. The action class must have a `run(self, gobi_file: GobiFile, recipes: dict[str, Recipe], actions: list[Action], args: list[str]) -> GobiError | None` function that will get triggered when the action is run.

The action must have a `name` and `subname` attribute they are used to identify the action when running gobi. The name must be unique for each action across the project, this is left to the recipe developer to enforce. We recommend using the recipe name as the prefix for the action name. The subname is a shorthand, gobi will attempt to match the subname, but if it is ambiguous, the full name must be specified.

The action class can also have a `help(self) -> str` method that returns a help message for the action.

Finally every recipe file must have a create() function that returns an instance of the recipe class.

The recipe can be loaded by adding the python file name to the `recipes` list in the gobi section of the gobi file without the .py extension.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.


