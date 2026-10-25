# bash completion for raml-validator — load with:  eval "$(raml-validator completion bash)"
_raml_validator() {
  local cur prev cmd
  cur="${COMP_WORDS[COMP_CWORD]}"
  prev="${COMP_WORDS[COMP_CWORD-1]}"
  cmd="${COMP_WORDS[1]}"
  if [ "$COMP_CWORD" -eq 1 ]; then
    COMPREPLY=($(compgen -W "audit fix run verify setup completion --version --help" -- "$cur"))
    return
  fi
  case "$prev" in
    --lang) COMPREPLY=($(compgen -W "en fr" -- "$cur")); return ;;
    --out-dir|--root) COMPREPLY=($(compgen -d -- "$cur")); return ;;
    --api-description) return ;;
  esac
  case "$cmd" in
    audit|fix|run)
      if [[ "$cur" == -* ]]; then
        COMPREPLY=($(compgen -W "--out-dir --lang --api-description --no-color --help" -- "$cur"))
      else
        COMPREPLY=($(compgen -f -X '!*.raml' -- "$cur") $(compgen -d -- "$cur"))
      fi ;;
    verify) COMPREPLY=($(compgen -W "--root --help" -- "$cur")) ;;
    completion) COMPREPLY=($(compgen -W "zsh bash powershell" -- "$cur")) ;;
  esac
}
complete -o filenames -F _raml_validator raml-validator
