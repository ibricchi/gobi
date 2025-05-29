#compdef gobi

# take arguments from 'gobi [args]'
# call 'gobi_cli completion [args]' to generate options
_gobi() {
    local -a completions
    local -a args

    args=("${(@)words[2,-2]}")
    
    # Get completions from gobi_cli
    completions=("${(@f)$(gobi_cli completion $args)}")
    
    # propose completions
    if [[ -n $completions ]]; then
        _describe 'gobi options' completions
    else
        # If no completions, fallback to default behavior
        _arguments '*: :->args'
    fi
}

compdef _gobi gobi
