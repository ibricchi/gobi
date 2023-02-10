#!/bin/bash

_gobi_complete() {
    if [ "${#COMP_WORDS[@]}" == 2 ]; then
        cur="${COMP_WORDS[COMP_CWORD]}"
        opts=$(gobi list | tail +2)
        COMPREPLY=( $(compgen -W "${opts}" ${cur}) )
    fi
    if [ "${#COMP_WORDS[@]}" == 3 ]; then
        prev="${COMP_WORDS[COMP_CWORD-1]}"
        cur="${COMP_WORDS[COMP_CWORD]}"
        opts=$(gobi "$prev" list | tail +2)
        COMPREPLY=( $(compgen -W "${opts}" ${cur}) )
    fi
}

complete -F _gobi_complete gobi
complete -F _gobi_complete gobi.py