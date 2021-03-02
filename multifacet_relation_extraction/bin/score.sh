#!/bin/bash
conf=$1
run=$2
name=$3
partition=$4
other_args=${@:5}

# TODO:Make sure the model folder name contains the basis number - VVIMP
source $conf
if [[ -z "${randomness}" ]]
then
    randomness=""
else
    if [[ "${randomness}" == true ]]
    then
        randomness="--randomness True"
    else
        randomness="--randomness False"
    fi
fi
if [[ -z "${n_basis_kb}" ]]; then n_basis_kb=""; else n_basis_kb="--n_basis_kb ${n_basis_kb}"; fi
if [[ -z "${epochs}" ]]; then num_epochs=1; else num_epochs="${#epochs[@]}"; fi
if [[ -z "${data}" ]]; then data=""; else data="--data ${data}"; fi
for (( i=0; i < ${num_epochs}; i++)); do
  if [[ -z "${epochs}" ]]; then ep=""; else ep="ep${epochs[$i]}"; fi
  if [[ -z "${spanish}" ]] || [[ "${spanish}" == false ]]; then
      spanish=""
      file="full_sentence_candidates_"
      suffix_arr=( "${years[@]}" )
  else
      spanish="--spanish"
      file="es_"
      suffix_arr=( "${suffixes[@]}" )
  fi
  for suffix in "${suffix_arr[@]}"; do
    cmds=()
    for n_basis in "${basis_arr[@]}"; do
      basis_str="b${n_basis}"
      while IFS= read -r -d $'\0' model_dir; do
        if [[ "${model_dir}" == *"${basis_str}"* || "${model_dir}" == *"basis${n_basis}"* ]] ; then
          mkdir -p "output/${run}/${model_type}/${basis_str}${ep}"
          cmd="${PY_PATH} src/testing/score.py ${data} --n_basis ${n_basis} ${n_basis_kb} --checkpoint ${model_dir}/${ep} --candidate_file data/candidates/${file}${suffix} --outf output/${run}/${model_type}/${basis_str}${ep}/${file}${suffix}_scored --batch_size ${batch_size} --de_model ${dec_type} --en_model ${enc_type} ${randomness} ${spanish}"
          case ${model_type} in
          trans)
            cmd="${cmd} --encode_trans_layers ${enc_layers} --trans_layers ${dec_layers}"
            ;;
          lstm)
            cmd="${cmd} --nhid ${nhid} --nhidlast2 ${nhidlast2} --positional_option ${positional_option} --nlayers ${enc_layers} --nlayers_dec ${dec_layers}"
            ;;
          lstm-trans)
            cmd="${cmd} --nhid ${nhid} --nlayers ${enc_layers} --trans_layers ${dec_layers} --positional_option ${positional_option}"
            ;;
          esac
          cmds+=("${cmd}")
        fi
      done< <(find models/ -name "${model_prefix}*" -print0)
    done
    if [[ -z "${partition}" ]]; then
      bash ./bin/run_score.sh "${cmds[@]}" &
    else
      sbatch --job-name="${name}_${suffix}_${ep}" --dependency=singleton --output="logs/score-${name}${ep}_${suffix}.txt" --err="logs/score-${name}${ep}_${suffix}.err" --partition="${partition}" --gres=gpu:1 ${other_args} bin/run_score.sh "${cmds[@]}"
    fi
  done
  if [[ -z "${partition}" ]]; then
    wait
  fi
done


