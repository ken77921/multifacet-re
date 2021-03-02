# Makefile to generate TAC-response. 
# Pipeline starts with query.xml and generates response.
#
# This produces a 2013 run merging the output from old and new modules.
#
# Author: Benjamin Roth

.SECONDARY:

modules=$(shell $(TAC_ROOT)/bin/get_config.sh modules default)

# copies query.xml from location specified in config file
query.xml:
	cp $(shell $(TAC_ROOT)/bin/get_expand_config.sh query.xml) $@

hop1_query.xml: query.xml
	$(TAC_ROOT)/components/bin/generate_queries2016.sh query.xml hop1_query.xml

# Adds expansiond to original queries and explicitly lists relations.
%_query_expanded.xml: %_query.xml
	$(TAC_ROOT)/components/bin/expand_query.sh $+ $@

%_query_expanded_within_doc.xml: %_query.xml
	$(TAC_ROOT)/components/bin/expand_query_within_doc.sh $+ $@

index:
	$(TAC_ROOT)/components/bin/create_index.sh $@

%_pp15_noNIL_filtered: %_pp15_noNIL
	$(TAC_ROOT)/components/bin/hop2_prefiltering.sh $+ $@

hop2_query.xml: query.xml hop1_response_$(modules)_pp15_noNIL_filtered
	$(TAC_ROOT)/components/bin/generate_queries2016.sh query.xml hop2_query.xml hop1_response_$(modules)_pp15_noNIL_filtered

#hop2_query.xml: query.xml hop1_response_$(modules)_pp15_noNIL
#	$(TAC_ROOT)/components/bin/generate_queries2016.sh query.xml hop2_query.xml hop1_response_$(modules)_pp15_noNIL
#$(TAC_ROOT)/components/tac2015/CS-GenerateQueries.pl hop1_query.xml hop2_query.xml hop1_response_$(modules)_pp15_noNIL


# Retrieves ranked list document ids/files.
%_dscore: %_query_expanded.xml index
	$(TAC_ROOT)/components/bin/retrieve_using_index.sh $+ $@

# Tokenizes/splits sentences from retrieved docs.
# Parallelized sentence splitting.
%_drank: %_query_expanded_within_doc.xml %_dscore
	$(TAC_ROOT)/components/bin/split_sentences2_parallel.sh $+ $@

# Tags sentences.
# Replaced relationfactory tagger by UMass tagger.
%_dtag: %_drank
	$(TAC_ROOT)/components/bin/umass_tagging_ajay.sh $+ $@

# Candidates from sentences where Query string and tags match.
%_candidates: %_query_expanded_within_doc.xml %_dtag %_dscore
	$(TAC_ROOT)/components/bin/candidates2013.sh $+ $@

%_candidates_inv_for_Pat: %_candidates
	$(TAC_ROOT)/components/bin/invert_candidates_for_Pat_model.sh $+ $@

# Converts candidates into protocol-buffer format.
%_candidates.pb: %_candidates
	$(TAC_ROOT)/components/bin/cands_to_proto.sh $+ $@

# Generates TAC-response with 'lsv' team id.

%_response_Pat_SES:
	cp $(shell $(TAC_ROOT)/bin/get_expand_config.sh Pat_SES_$*_result) $@

%_response_Pat_org:
	cp $(shell $(TAC_ROOT)/bin/get_expand_config.sh Pat_org_$*_result) $@

%_response_Pat_doc_exp_SES:
	cp $(shell $(TAC_ROOT)/bin/get_expand_config.sh Pat_doc_exp_SES_$*_result) $@

%_response_Pat_doc_exp_org:
	cp $(shell $(TAC_ROOT)/bin/get_expand_config.sh Pat_doc_exp_org_$*_result) $@

# Response from pattern matches.
%_response_patterns: %_query_expanded_within_doc.xml %_candidates.pb
	$(TAC_ROOT)/components/bin/pattern_response.sh $+ $@

# Response from matching query name expansions.
%_response_alternate_names: %_query_expanded.xml %_dtag %_dscore
	$(TAC_ROOT)/components/bin/alternate_names.sh $+ $@

hop1:
	mkdir -p $@

hop2:
	mkdir -p $@

hop1_response_2016_sf_run1: hop1_query_expanded_within_doc.xml hop1_response_Pat_doc_exp_org hop1_response_Pat_doc_exp_SES hop1_response_alternate_names hop1_response_patterns
	$(TAC_ROOT)/components/bin/merge_responses.sh $+ > $@

hop2_response_2016_sf_run1: hop2_query_expanded_within_doc.xml hop2_response_Pat_doc_exp_org
	$(TAC_ROOT)/components/bin/merge_responses.sh $+ > $@


hop1_response_2016_sf_run2: hop1_query_expanded.xml hop1_response_Pat_org hop1_response_Pat_SES hop1_response_alternate_names hop1_response_patterns
	$(TAC_ROOT)/components/bin/merge_responses.sh $+ > $@

hop2_response_2016_sf_run2: hop2_query_expanded.xml hop2_response_Pat_org
	$(TAC_ROOT)/components/bin/merge_responses.sh $+ > $@


hop1_response_2016_sf_run4: hop1_query_expanded_within_doc.xml hop1_response_Pat_doc_exp_org hop1_response_alternate_names hop1_response_patterns
	$(TAC_ROOT)/components/bin/merge_responses.sh $+ > $@

hop2_response_2016_sf_run4: hop2_query_expanded_within_doc.xml hop2_response_Pat_doc_exp_org
	$(TAC_ROOT)/components/bin/merge_responses.sh $+ > $@


hop1_response_2016_sf_run5: hop1_query_expanded_within_doc.xml hop1_response_Pat_doc_exp_SES hop1_response_alternate_names hop1_response_patterns
	$(TAC_ROOT)/components/bin/merge_responses.sh $+ > $@

hop2_response_2016_sf_run5: hop2_query_expanded_within_doc.xml hop2_response_Pat_doc_exp_SES
	$(TAC_ROOT)/components/bin/merge_responses.sh $+ > $@



hop1_%_ASCII: hop1_%
	$(TAC_ROOT)/components/bin/remove_special_characters.sh $+ $@
	#iconv -c -f UTF-8 -t ASCII $+ > $@

hop2_%_ASCII: hop2_%
	$(TAC_ROOT)/components/bin/remove_special_characters.sh $+ $@
	#iconv -c -f UTF-8 -t ASCII $+ > $@

# Postprocess response for 2015 format.
hop1_%_pp15: hop1_%_ASCII hop1_query_expanded_within_doc.xml /dev/null
	$(TAC_ROOT)/components/bin/postprocess2015.sh $+ $@

hop2_%_pp15: hop2_%_ASCII hop2_query_expanded_within_doc.xml /dev/null
	$(TAC_ROOT)/components/bin/postprocess2015.sh $+ $@

%_noNIL: %
	$(TAC_ROOT)/components/bin/response_cs_sf.sh $+ $@
#	grep -v NIL $+ | sed '/\&amp;/! s/\&/\&amp;/g' | iconv -c -f UTF-8 -t ASCII > $@


#response_packaged: hop1_query.xml hop1_response_$(modules)_pp15_noNIL hop2_response_$(modules)_pp15_noNIL
response_packaged: query.xml hop1_response_$(modules)_pp15_noNIL hop2_response_$(modules)_pp15_noNIL
	$(TAC_ROOT)/evaluation/bin/2016_04/package_kb_2016.sh $+ $@

### 2015 eval ###

docs_list:
	cp $(shell $(TAC_ROOT)/bin/get_expand_config.sh doclengths) $@

assessments:
	cp $(shell $(TAC_ROOT)/bin/get_expand_config.sh assessments) $@

#response_packaged_2015: hop1_query.xml hop1_response_$(modules)_pp15_noNIL hop2_response_$(modules)_pp15_noNIL
#	$(TAC_ROOT)/evaluation/bin/2015/package_kb_2015_new.sh $+ $@

#response_fix_hop2_qid_2015: response_packaged docs_list query.xml
#	$(TAC_ROOT)/evaluation/bin/2015/fix_hop2_qid_2015.sh $+ $@

response_validated: response_packaged docs_list query.xml
	$(TAC_ROOT)/evaluation/bin/2016_04/validate_sf.sh $+ $@ 16

eval_2015: query.xml response_validated assessments
	$(TAC_ROOT)/evaluation/bin/2016_04/eval.sh $+ $@ 16

