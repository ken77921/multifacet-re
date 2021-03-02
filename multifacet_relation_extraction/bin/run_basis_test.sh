#!/bin/bash

$PY_PATH src/testing/basis_test.py --n_basis 5 --n_basis_kb 11 --checkpoint models/milestone_run_trans-b5-kb11-20200604-162512/ep50/ --data "$DATA_DIR" --entpair_vocab_map "${DATA_DIR%/}"/entpair-new-vocab.txt --outf output/milestone_run_trans-b5-kb11/trans/b5ep50/gen_basis.txt --max_batch_num 2000 --batch_size 200 --de_model TRANS --en_model TRANS --encode_trans_layers 3 --trans_layers 3 --randomness False --seed 11
