#!/bin/bash

conf=$1
name=$2

if [ ! -e $conf ]; then
    echo "No config file specified; Exiting."
    exit 1
fi

source $conf

model_dir="./models/${name}"
if [[ -z "${data}" ]]; then data=""; else data="--data ${data}"; fi
if [[ -z "${tensor_folder}" ]]; then tensor_folder=""; else tensor_folder="--tensor_folder ${tensor_folder}"; fi
if [[ -z "${training_file}" ]]; then training_file=""; else training_file="--training_file ${training_file}"; fi
if [[ -z "${source_emsize}" ]]; then source_emsize=""; else source_emsize="--source_emsize ${source_emsize}"; fi

if [[ -z "${update_source_emb}" ]]
then
    update_source_emb=""
else
    if [[ "${update_source_emb}" == true ]]
    then
        update_source_emb="--update_source_emb"
    else
        update_source_emb=""
    fi
fi

if [[ -z "${source_emb_file}" ]]; then source_emb_file=""; else source_emb_file="--source_emb_file ${source_emb_file}"; fi
if [[ -z "${source_emb_source}" ]]; then source_emb_source=""; else source_emb_source="--source_emb_source ${source_emb_source}"; fi
if [[ -z "${target_emsize}" ]]; then target_emsize=""; else target_emsize="--target_emsize ${target_emsize}"; fi

if [[ -z "${update_target_emb}" ]]
then
    update_target_emb=""
else
    if [[ "${update_target_emb}" == true ]]
    then
        update_target_emb="--update_target_emb"
    else
        update_target_emb=""
    fi
fi

if [[ -z "${target_emb_source}" ]]; then target_emb_source=""; else target_emb_source="--target_emb_source ${target_emb_source}"; fi
if [[ -z "${target_emb_file}" ]]; then target_emb_file=""; else target_emb_file="--target_emb_file ${target_emb_file}"; fi
if [[ -z "${en_model}" ]]; then en_model=""; else en_model="--en_model ${en_model}"; fi
if [[ -z "${dropouti}" ]]; then dropouti=""; else dropouti="--dropouti ${dropouti}"; fi
if [[ -z "${dropoute}" ]]; then dropoute=""; else dropoute="--dropoute ${dropoute}"; fi
if [[ -z "${dropout}" ]]; then dropout=""; else dropout="--dropout ${dropout}"; fi
if [[ -z "${nhid}" ]]; then nhid=""; else nhid="--nhid ${nhid}"; fi
if [[ -z "${nlayers}" ]]; then nlayers=""; else nlayers="--nlayers ${nlayers}"; fi
if [[ -z "${nlayers_dec}" ]]; then nlayers_dec=""; else nlayers_dec="--nlayers_dec ${nlayers_dec}"; fi
if [[ -z "${encode_trans_layers}" ]]; then encode_trans_layers=""; else encode_trans_layers="--encode_trans_layers ${encode_trans_layers}"; fi
if [[ -z "${trans_nhid}" ]]; then trans_nhid=""; else trans_nhid="--trans_nhid ${trans_nhid}"; fi
if [[ -z "${de_model}" ]]; then de_model=""; else de_model="--de_model ${de_model}"; fi
if [[ -z "${de_coeff_model}" ]]; then de_coeff_model=""; else de_coeff_model="--de_coeff_model ${de_coeff_model}"; fi
if [[ -z "${n_basis}" ]]; then n_basis=""; else n_basis="--n_basis ${n_basis}"; fi
if [[ -z "${n_basis_kb}" ]]; then n_basis_kb=""; else n_basis_kb="--n_basis_kb ${n_basis_kb}"; fi
if [[ -z "${positional_option}" ]]; then positional_option=""; else positional_option="--positional_option ${positional_option}"; fi
if [[ -z "${dropoutp}" ]]; then dropoutp=""; else dropoutp="--dropoutp ${dropoutp}"; fi
if [[ -z "${nhidlast2}" ]]; then nhidlast2=""; else nhidlast2="--nhidlast2 ${nhidlast2}"; fi
if [[ -z "${dropout_prob_lstm}" ]]; then dropout_prob_lstm=""; else dropout_prob_lstm="--dropout_prob_lstm ${dropout_prob_lstm}"; fi
if [[ -z "${trans_layers}" ]]; then trans_layers=""; else trans_layers="--trans_layers ${trans_layers}"; fi

if [[ -z "${de_en_connection}" ]]
then
    de_en_connection=""
else
    if [[ "${de_en_connection}" == true ]]
    then
        de_en_connection="--de_en_connection True"
    else
        de_en_connection="--de_en_connection False"
    fi
fi
if [[ -z "${dropout_prob_trans}" ]]; then dropout_prob_trans=""; else dropout_prob_trans="--dropout_prob_trans ${dropout_prob_trans}"; fi
if [[ -z "${w_loss_coeff}" ]]; then w_loss_coeff=""; else w_loss_coeff="--w_loss_coeff ${w_loss_coeff}"; fi
if [[ -z "${L1_losss_B}" ]]; then L1_losss_B=""; else L1_losss_B="--L1_losss_B ${L1_losss_B}"; fi
if [[ -z "${coeff_opt}" ]]; then coeff_opt=""; else coeff_opt="--coeff_opt ${coeff_opt}"; fi
if [[ -z "${coeff_opt_algo}" ]]; then coeff_opt_algo=""; else coeff_opt_algo="--coeff_opt_algo ${coeff_opt_algo}"; fi
if [[ -z "${optimizer}" ]]; then optimizer=""; else optimizer="--optimizer ${optimizer}"; fi
if [[ -z "${optimizer_target}" ]]; then optimizer_target=""; else optimizer_target="--optimizer_target ${optimizer_target}"; fi
if [[ -z "${optimizer_auto}" ]]; then optimizer_auto=""; else optimizer_auto="--optimizer_auto ${optimizer_auto}"; fi
if [[ -z "${lr}" ]]; then lr=""; else lr="--lr ${lr}"; fi
if [[ -z "${lr2_divide}" ]]; then lr2_divide=""; else lr2_divide="--lr2_divide ${lr2_divide}"; fi
if [[ -z "${auto_w}" ]]; then auto_w=""; else auto_w="--auto_w ${auto_w}"; fi
if [[ -z "${lr_auto}" ]]; then lr_auto=""; else lr_auto="--lr_auto ${lr_auto}"; fi
if [[ -z "${clip}" ]]; then clip=""; else clip="--clip ${clip}"; fi
if [[ -z "${epochs}" ]]; then epochs=""; else epochs="--epochs ${epochs}"; fi
if [[ -z "${batch_size}" ]]; then batch_size=""; else batch_size="--batch_size ${batch_size}"; fi
if [[ -z "${small_batch_size}" ]]; then small_batch_size=""; else small_batch_size="--small_batch_size ${small_batch_size}"; fi
if [[ -z "${loss}" ]]; then loss=""; else loss="--loss ${loss}"; fi
if [[ -z "${eps}" ]]; then eps=""; else eps="--eps ${eps}"; fi
if [[ -z "${wdecay}" ]]; then wdecay=""; else wdecay="--wdecay ${wdecay}"; fi
if [[ -z "${wdecay_target}" ]]; then wdecay_target=""; else wdecay_target="--wdecay_target ${wdecay_target}"; fi
if [[ -z "${nonmono}" ]]; then nonmono=""; else nonmono="--nonmono ${nonmono}"; fi
if [[ -z "${warmup_proportion}" ]]; then warmup_proportion=""; else warmup_proportion="--warmup_proportion ${warmup_proportion}"; fi
if [[ -z "${training_split_num}" ]]; then training_split_num=""; else training_split_num="--training_split_num ${training_split_num}"; fi
if [[ -z "${valid_per_epoch}" ]]; then valid_per_epoch=""; else valid_per_epoch="--valid_per_epoch ${valid_per_epoch}"; fi

if [[ -z "${copy_training}" ]]
then
    copy_training=""
else
    if [[ "${copy_training}" == true ]]
    then
        copy_training="--copy_training True"
    else
        copy_training="--copy_training False"
    fi
fi
if [[ -z "${seed}" ]]; then seed=""; else seed="--seed ${seed}"; fi

if [[ -z "${cuda}" ]]
then
    cuda=""
else
    if [[ "${cuda}" == true ]]
    then
        cuda="--cuda True"
    else
        cuda="--cuda False"
    fi
fi

if [[ -z "${auto_avg}" ]]
then
    auto_avg=""
else
    if [[ "${auto_avg}" == true ]]
    then
        auto_avg="--auto_avg True"
    else
        auto_avg="--auto_avg False"
    fi
fi

if [[ -z "${pre_avg}" ]]
then
    pre_avg=""
else
    if [[ "${pre_avg}" == true ]]
    then
        pre_avg="--pre_avg True"
    else
        pre_avg="--pre_avg False"
    fi
fi

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

if [[ -z "${single_gpu}" ]]
then
    single_gpu=""
else
    if [[ "${single_gpu}" == true ]]
    then
        single_gpu="--single_gpu"
    else
        single_gpu=""
    fi
fi

if [[ -z "${rare}" ]]
then
    rare=""
else
    if [[ "${rare}" == true ]]
    then
        rare="--rare"
    else
        rare=""
    fi
fi

if [[ -z "${uniform_src}" ]]
then
    uniform_src=""
else
    if [[ "${uniform_src}" == true ]]
    then
        uniform_src="--uniform_src"
    else
        uniform_src=""
    fi
fi


if [[ -z "${skip_val}" ]]
then
    skip_val=""
else
    if [[ "${skip_val}" == true ]]
    then
        skip_val="--skip_val"
    else
        skip_val=""
    fi
fi


if [[ -z "${log_interval}" ]]; then log_interval=""; else log_interval="--log_interval ${log_interval}"; fi

if [[ -z "${continue_train}" ]]
then
    continue_train=""
else
    if [[ "${continue_train}" == true ]]
    then
        continue_train="--continue_train"
    else
        continue_train=""
    fi
fi


cmd="${PY_PATH} -u src/main.py \
--save ${model_dir} \
${data} \
${tensor_folder} \
${training_file} \
${source_emsize} \
${update_source_emb} \
${source_emb_file} \
${source_emb_source} \
${target_emsize} \
${update_target_emb} \
${target_emb_source} \
${target_emb_file} \
${en_model} \
${dropouti} \
${dropoute} \
${dropout} \
${nhid} \
${nlayers} \
${nlayers_dec} \
${encode_trans_layers} \
${trans_nhid} \
${de_model} \
${de_coeff_model} \
${n_basis} \
${n_basis_kb} \
${positional_option} \
${dropoutp} \
${nhidlast2} \
${dropout_prob_lstm} \
${trans_layers} \
${de_en_connection} \
${dropout_prob_trans} \
${w_loss_coeff} \
${L1_losss_B} \
${coeff_opt} \
${coeff_opt_algo} \
${optimizer} \
${optimizer_target} \
${optimizer_auto} \
${lr} \
${lr2_divide} \
${clip} \
${epochs} \
${batch_size} \
${small_batch_size} \
${loss} \
${wdecay} \
${wdecay_target} \
${nonmono} \
${warmup_proportion} \
${training_split_num} \
${valid_per_epoch} \
${copy_training} \
${seed} \
${cuda} \
${randomness} \
${single_gpu} \
${log_interval} \
${continue_train} \
${rare} \
${skip_val} \
${auto_w} \
${lr_auto} \
${auto_avg} \
${pre_avg} \
${uniform_src}"

echo ${cmd}
eval ${cmd}