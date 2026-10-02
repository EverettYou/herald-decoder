const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const {chromium}=require('/Users/home/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const LAB=path.resolve(__dirname,'..'),ROOT=path.resolve(LAB,'../..'),id=path.basename(LAB),base='http://127.0.0.1:8010';
const read=p=>fs.readFileSync(p,'utf8'),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
async function get(url){const r=await fetch(base+url);assert.equal(r.status,200,url);return r.json();}
async function main(){
 const meta=JSON.parse(read(path.join(LAB,'lab.json'))),api=await get('/api/labs/'+id);
 const reg=JSON.parse(read(path.join(ROOT,'labs/labs.json'))).labs.find(x=>x.id===id);
 for(const k of ['stage','current_focus','next_action']){assert.equal(api.lab[k],meta[k]);assert.equal(reg[k],meta[k]);}
 assert.equal(api.report.content,read(path.join(LAB,'REPORT.md')));assert.equal(api.plan.content,read(path.join(LAB,'PLAN.md')));
 assert.equal(meta.results.filter(x=>x.id==='square-midpoint-thermodynamics').length,1);
 const result=JSON.parse(read(path.join(LAB,'results/square-midpoint-thermodynamics-2026-09-20.json')));
 assert.equal(result.status,'passed');assert.equal(result.current_states,256);assert.equal(result.bond_control_states,256);
 assert.equal(result.Bayes_LER_exact,'7/16');assert.equal(result.support_equivalence_failures,0);
 for(const [file,h] of Object.entries(result.source_sha256))assert.equal(sha(path.join(ROOT,file)),h,file);
 const posterior=JSON.parse(read(path.join(LAB,'results/posterior-balance-polynomial-2026-09-20.json')));
 assert.equal(posterior.status,'complete_obstruction');assert.equal(posterior.new_physical_record_samples,0);
 assert.equal(posterior.identity_failures,0);assert.equal(posterior.L3_root_control.all_records_real_nonpositive,true);
 assert.equal(posterior.decision.threshold_claim,'No square decoding threshold or midpoint noncorrectability follows from this bounded control.');
 for(const [file,h] of Object.entries(posterior.source_sha256))assert.equal(sha(path.join(ROOT,file)),h,file);
 const closure=JSON.parse(read(path.join(LAB,'results/posterior-polynomial-closure-2026-09-20.json')));
 assert.equal(closure.status,'complete_recurrence_obstruction');assert.equal(closure.exhaustive_current_states,262144);
 assert.equal(closure.transfer_validation.final_real_nonpositive_root_failures,0);
 assert.equal(closure.transfer_validation.actual_pair_interlacing_failures,0);
 assert.equal(closure.common_family_interlacing_counterexample.first_polynomial,'t');
 assert.equal(closure.common_family_interlacing_counterexample.second_polynomial,'1+5t+t^2');
 assert.equal(closure.decision.threshold_claim,'No square midpoint or decoding-threshold claim is promoted.');
 for(const [file,h] of Object.entries(closure.source_sha256))assert.equal(sha(path.join(ROOT,file)),h,file);
 const switching=JSON.parse(read(path.join(LAB,'results/midpoint-switching-pairing-2026-09-20.json')));
 assert.equal(switching.status,'complete_selector_obstruction');assert.equal(switching.new_physical_record_samples,0);
 assert.equal(switching.decoder_runs,0);assert.equal(switching.size_audits.length,2);
 const switchL4=switching.size_audits.find(x=>x.L===4);assert(switchL4);
 assert.equal(switchL4.path_flip_charge_preservation_failures,0);
 assert.equal(switchL4.path_flip_logical_parity_failures,0);
 assert.equal(switchL4.lower_extremal_selector.eligible_crossing_states,232822);
 assert.equal(switchL4.lower_extremal_selector.selector_stable_states,113412);
 assert.equal(switchL4.lower_extremal_selector.all_eligible_map_injective,false);
 assert.equal(switchL4.lower_extremal_selector.all_eligible_map_maximum_multiplicity,16);
 assert.equal(switchL4.local_plaquette.logical_parity_flip_successes,0);
 assert.equal(switching.decision.threshold_claim,'No square midpoint or decoding-threshold claim is promoted.');
 for(const [file,h] of Object.entries(switching.source_sha256))assert.equal(sha(path.join(ROOT,file)),h,file);
 const fractional=JSON.parse(read(path.join(LAB,'results/midpoint-fractional-switching-2026-09-20.json')));
 assert.equal(fractional.status,'complete_finite_saturation_missing_uniform_theorem');
 assert.equal(fractional.new_physical_record_samples,0);assert.equal(fractional.decoder_runs,0);
 const fractionalL4=fractional.size_audits.find(x=>x.L===4);assert(fractionalL4);
 assert.equal(fractionalL4.unique_switching_edges,580608);
 assert.equal(fractionalL4.maximum_integral_matching_pairs,94792);
 assert.equal(fractionalL4.bayes_numerator_sum_min_sector_counts,94792);
 assert.equal(fractionalL4.record_saturation_failures,0);
 assert.equal(fractionalL4.fractional_certificate.fractional_optimum_equals_integral_optimum,true);
 assert.equal(fractionalL4.dual_vertex_cover.uncovered_switching_edges,0);
 assert.equal(fractional.decision.threshold_claim,'No square midpoint noncorrectability or decoding-threshold claim is promoted.');
 for(const [file,h] of Object.entries(fractional.source_sha256))assert.equal(sha(path.join(ROOT,file)),h,file);
 const orientation=JSON.parse(read(path.join(LAB,'results/midpoint-all-size-matching-theorem-2026-09-20.json')));
 assert.equal(orientation.status,'complete_missing_restricted_orientation_NMP_theorem');
 assert.equal(orientation.new_physical_record_samples,0);assert.equal(orientation.decoder_runs,0);
 const orientationL4=orientation.canonical_size_audits.find(x=>x.L===4);assert(orientationL4);
 assert.equal(orientationL4.orientation_embedding.alpha_orientation_embedding,true);
 assert.equal(orientationL4.normalized_transport.transport_target,1253808);
 assert.equal(orientationL4.normalized_transport.transport_achieved,1253808);
 assert.equal(orientationL4.restricted_graph_fragmentation.ambiguous_records_split_into_multiple_switching_components,578);
 assert.equal(orientationL4.internal_directed_plaquette_states,86528);
 assert.equal(orientation.counterexample_matrix.single_edge_deletions_tested,18);
 assert.equal(orientation.counterexample_matrix.double_edge_deletions_tested,153);
 assert.equal(orientation.counterexample_matrix.first_Hall_gap,null);
 assert.equal(orientation.decision.threshold_claim,'No square midpoint noncorrectability or decoding-threshold claim is promoted.');
 for(const [file,h] of Object.entries(orientation.source_sha256))assert.equal(sha(path.join(ROOT,file)),h,file);
 const minority=JSON.parse(read(path.join(LAB,'results/midpoint-minority-mass-lower-bound-2026-09-20.json')));
 assert.equal(minority.status,'complete_rsw_and_nmp_information_obstruction');
 assert.equal(minority.new_physical_record_samples,0);assert.equal(minority.decoder_runs,0);
 const minorityL4=minority.finite_controls.find(x=>x.L===4);assert(minorityL4);
 assert.equal(minorityL4.selector_maximum_congestion,16);
 assert.equal(minorityL4.bounded_congestion_certificate_exact,'116411/2228224');
 assert.equal(minority.information_theoretic_countermodel.graph_family,'complete bipartite K_{1,M}');
 assert.equal(minority.information_theoretic_countermodel.normalized_matching_property,true);
 assert.equal(minority.information_theoretic_countermodel.minority_fraction,'1/(M+1)');
 assert.equal(minority.branch_matrix.crossing_or_arm_event.outcome,'ordinary_RSW_is_insufficient');
 assert.equal(minority.decision.threshold_claim,'No square midpoint noncorrectability or decoding-threshold claim is promoted.');
 for(const [file,h] of Object.entries(minority.source_sha256))assert.equal(sha(path.join(ROOT,file)),h,file);
 const balance=JSON.parse(read(path.join(LAB,'results/midpoint-charge-fiber-balance-theorem-2026-09-20.json')));
 assert.equal(balance.status,'complete_finite_balance_controls_missing_averaged_theorem');
 assert.equal(balance.new_physical_record_samples,0);assert.equal(balance.decoder_runs,0);
 const balanceL4=balance.exact_controls.find(x=>x.L===4);assert(balanceL4);
 assert.equal(balanceL4.optimal_deterministic_switching_congestion,6);
 assert.equal(balanceL4.extremal_selector_congestion,16);
 assert.equal(balanceL4.maximum_charge_fiber_sector_ratio_exact,'6');
 assert.equal(balanceL4.records_attaining_maximum_ratio,96);
 assert.equal(balanceL4.physical_mass_of_maximum_ratio_records_exact,'21/8192');
 assert.equal(balanceL4.first_maximum_ratio_witness.switching_graph,'K_{1,6}');
 assert(Math.abs(balanceL4.conditional_logical_entropy_bits-0.8514082240002299)<1e-15);
 assert.equal(balance.decision.threshold_claim,'No square midpoint noncorrectability or decoding-threshold claim is promoted.');
 for(const [file,h] of Object.entries(balance.source_sha256))assert.equal(sha(path.join(ROOT,file)),h,file);
 const average=JSON.parse(read(path.join(LAB,'results/midpoint-averaged-charge-balance-2026-09-20.json')));
 assert.equal(average.status,'complete_overlap_and_block_routes_missing_global_average_lemma');
 assert.equal(average.new_physical_record_samples,0);assert.equal(average.decoder_runs,0);
 const averageL4=average.exact_controls.find(x=>x.L===4);assert(averageL4);
 assert.equal(averageL4.same_charge_collision_probability_exact,'653081/8589934592');
 assert.equal(averageL4.opposite_sector_same_charge_overlap_exact,'78363/2147483648');
 assert.equal(averageL4.collision_conditioned_opposite_sector_probability_exact,'313452/653081');
 assert.equal(averageL4.collision_to_maximum_record_probability_exact,'653081/4423680');
 assert.equal(averageL4.physical_mass_with_minority_ratio_at_least['1/8'],'116411/131072');
 assert.equal(average.branch_matrix.two_copy_overlap.outcome,'exact_observable_but_collision_bias_blocks_asymptotic_conversion');
 assert.equal(average.branch_matrix.multiscale_block.outcome,'local_gluing_does_not_supply_logical_charge_balance');
 assert.equal(average.decision.threshold_claim,'No square midpoint noncorrectability or decoding-threshold claim is promoted.');
 for(const [file,h] of Object.entries(average.source_sha256))assert.equal(sha(path.join(ROOT,file)),h,file);
 const collision=JSON.parse(read(path.join(LAB,'results/midpoint-charge-collision-comparison-2026-09-20.json')));
 assert.equal(collision.status,'complete_existing_theorems_do_not_give_dimension_free_conversion');
 assert.equal(collision.new_physical_record_samples,0);assert.equal(collision.decoder_runs,0);
 const collisionL4=collision.exact_controls.find(x=>x.L===4);assert(collisionL4);
 assert.equal(collisionL4.measured_charge_dimension,8);
 assert.equal(collisionL4.coordinate_line_log_concavity.tested_neighbor_triples,125616);
 assert.equal(collisionL4.coordinate_line_log_concavity.violations,0);
 assert.equal(collisionL4.bitwise_complement_sector_action,'preserves_logical_sector');
 assert.equal(collision.branch_matrix.local_limit_or_anti_concentration.outcome,'existing_results_do_not_supply_the_required_growing_dimension_atom_comparison');
 assert.equal(collision.branch_matrix.collision_weighted_sector_balance.outcome,'no_structural_lower_bound_on_Psi_L');
 assert.equal(collision.decision.threshold_claim,'No square midpoint noncorrectability or decoding-threshold claim is promoted.');
 for(const [file,h] of Object.entries(collision.source_sha256))assert.equal(sha(path.join(ROOT,file)),h,file);
 const direct=JSON.parse(read(path.join(LAB,'results/midpoint-direct-risk-renormalization-2026-09-20.json')));
 assert.equal(direct.status,'complete_direct_reduction_missing_uniform_average_congestion');
 assert.equal(direct.new_physical_record_samples,0);assert.equal(direct.decoder_runs,0);
 const directL4=direct.exact_controls.find(x=>x.L===4);assert(directL4);
 assert.equal(directL4.lower_extremal_selector.effective_size_biased_multiplicity_exact,'76181/23005');
 assert.equal(directL4.lower_extremal_selector.Cauchy_direct_risk_lower_bound_exact,'1587690075/9985196032');
 assert.equal(directL4.upper_extremal_selector.effective_size_biased_multiplicity_exact,'76171/23005');
 assert.deepEqual(directL4.natural_charge_reveal.Bayes_risk_exact.slice(0,-1),Array(8).fill('1/2'));
 assert.equal(direct.branch_matrix.full_record_renormalized_switching.outcome,'exact_direct_reduction_but_missing_uniform_second_moment_bound');
 assert.equal(direct.decision.threshold_claim,'No square midpoint noncorrectability or decoding-threshold claim is promoted.');
 for(const [file,h] of Object.entries(direct.source_sha256))assert.equal(sha(path.join(ROOT,file)),h,file);
 const selector=JSON.parse(read(path.join(LAB,'results/midpoint-selector-second-moment-renormalization-2026-09-20.json')));
 assert.equal(selector.status,'complete_collision_identity_missing_summable_arm_bound');
 assert.equal(selector.new_physical_record_samples,0);assert.equal(selector.decoder_runs,0);
 const selectorL4=selector.exact_controls.find(x=>x.L===4);assert(selectorL4);
 assert.equal(selectorL4.order_matrix.lexicographic_lower.kappa_exact,'76181/23005');
 assert.equal(selectorL4.order_matrix.shortest_then_lexicographic.kappa_exact,'3113/1605');
 assert.equal(selectorL4.order_matrix.shortest_then_lexicographic.direct_risk_lower_bound_exact,'110769075/408027136');
 assert.equal(selectorL4.order_matrix.shortest_then_lexicographic.paired_identity.replayed,true);
 assert.equal(selectorL4.finite_family_summary.best_order,'shortest_then_lexicographic');
 assert.equal(selector.branch_matrix.arm_event_theorem_audit.outcome,'standard_arm_results_do_not_bound_full_record_selector_collisions');
 assert.equal(selector.decision.threshold_claim,'No square midpoint noncorrectability or decoding-threshold claim is promoted.');
 for(const [file,h] of Object.entries(selector.source_sha256))assert.equal(sha(path.join(ROOT,file)),h,file);
 const exchange=JSON.parse(read(path.join(LAB,'results/midpoint-shortest-selector-geodesic-exchange-2026-09-20.json')));
 assert.equal(exchange.status,'complete_two_environment_geodesic_exchange_gap');
 assert.equal(exchange.new_physical_record_samples,0);assert.equal(exchange.decoder_runs,0);
 const exchangeL3=exchange.exact_controls.find(x=>x.L===3),exchangeL4=exchange.exact_controls.find(x=>x.L===4);
 assert.equal(exchangeL3.kappa_exact,'11/9');assert.equal(exchangeL4.kappa_exact,'3113/1605');
 assert.equal(exchangeL3.exchange_matrix.same_physical_endpoints_closed_cycle_pairs.count,0);
 assert.equal(exchangeL4.exchange_matrix.same_physical_endpoints_closed_cycle_pairs.count,4170);
 assert.equal(exchangeL4.exchange_matrix.equal_path_length_pairs.count,7586);
 assert.equal(exchangeL4.collision_fan_control.preimage_mass_at_multiplicity_at_least_4.count,7528);
 assert.equal(exchangeL4.collision_fan_control.maximum_multiplicity,8);
 assert.equal(exchange.decision.threshold_claim,'No threshold claim is promoted.');
 for(const [file,h] of Object.entries(exchange.source_sha256))assert.equal(sha(path.join(ROOT,file)),h,file);
 const fan=JSON.parse(read(path.join(LAB,'results/midpoint-boundary-fan-tail-2026-09-21.json')));
 assert.equal(fan.status,'complete_witness_injection_conditioning_gap_and_bounded_template');
 assert.equal(fan.new_physical_record_samples,0);assert.equal(fan.decoder_runs,0);
 const fanL3=fan.exact_controls.find(x=>x.L===3),fanL4=fan.exact_controls.find(x=>x.L===4);
 assert.equal(fanL3.tail_sum_exact,'11/9');assert.equal(fanL4.tail_sum_exact,'3113/1605');
 assert.equal(fanL3.two_environment_witness.injective_on_exact_control,true);
 assert.equal(fanL4.two_environment_witness.ordered_alternate_preimages,129688);
 assert.deepEqual(fan.diamond_chain_templates.map(x=>x.maximum_multiplicity),[1,2,4,8]);
 assert.equal(fan.branch_matrix.disjoint_occurrence_probability.outcome,'BK_Reimer_product_measure_interface_fails_twice');
 assert.equal(fan.decision.threshold_claim,'No threshold claim is promoted.');
 for(const [file,h] of Object.entries(fan.source_sha256))assert.equal(sha(path.join(ROOT,file)),h,file);
 const strip=JSON.parse(read(path.join(LAB,'results/midpoint-boundary-fan-strip-transfer-2026-09-21.json')));
 assert.equal(strip.status,'complete_embedded_controls_and_selector_transfer_state_obstruction');
 assert.equal(strip.new_physical_record_samples,0);assert.equal(strip.decoder_runs,0);
 const stripW3=strip.direct_controls.find(x=>x.width_columns===3),stripW4=strip.direct_controls.find(x=>x.width_columns===4);
 assert.equal(stripW3.kappa_exact,'11/9');assert.equal(stripW4.kappa_exact,'3984/1963');
 assert.equal(stripW4.physical_majority_domain_states,3926);assert.equal(stripW4.selector_second_moment,7968);
 assert.equal(stripW4.maximum_multiplicity,5);
 const transferW5=strip.charge_majority_transfer.completed_widths.find(x=>x.width_columns===5);
 assert.equal(transferW5.physical_majority_domain_states,108978);assert.equal(transferW5.exact_Bayes_numerator,55496);
 assert.equal(strip.charge_majority_transfer.cap_hit.states_observed_before_fail_closed,2000001);
 assert.equal(strip.branch_matrix.selector_second_moment_transfer.outcome,'full_charge_transfer_does_not_carry_the_nonlocal_selector_moment');
 assert.equal(strip.decision.threshold_claim,'No threshold claim is promoted.');
 for(const [file,h] of Object.entries(strip.source_sha256))assert.equal(sha(path.join(ROOT,file)),h,file);
 const automaton=JSON.parse(read(path.join(LAB,'results/midpoint-selector-automaton-feasibility-2026-09-21.json')));
 assert.equal(automaton.status,'complete_exact_W5_selector_moment_with_bounded_reduced_automaton');
 assert.equal(automaton.new_physical_record_samples,0);assert.equal(automaton.decoder_runs,0);
 const autoW3=automaton.width_controls.find(x=>x.width_columns===3),autoW4=automaton.width_controls.find(x=>x.width_columns===4),autoW5=automaton.width_controls.find(x=>x.width_columns===5);
 assert.equal(autoW3.selector_second_moment,154);assert.equal(autoW4.selector_second_moment,7968);
 assert.equal(autoW5.physical_majority_domain_states,108978);assert.equal(autoW5.selector_second_moment,336814);
 assert.equal(autoW5.kappa_exact,'168407/54489');assert.equal(autoW5.maximum_multiplicity,12);
 assert.equal(autoW5.reduced_selector_mtbdd.total_states,179446);
 assert.equal(autoW5.reduced_selector_mtbdd.truth_table_replay_mismatches,0);
 assert.equal(autoW5.target_pair_accumulator.ordered_pair_count,227836);
 assert.equal(automaton.branch_matrix.analytic_embedded_subfamily.outcome,'not_reached_because_both_exact_branches_passed');
 assert.equal(automaton.decision.threshold_claim,'No threshold claim is promoted.');
 for(const [file,h] of Object.entries(automaton.source_sha256))assert.equal(sha(path.join(ROOT,file)),h,file);
 const rate=JSON.parse(read(path.join(LAB,'results/midpoint-selector-rate-certificate-2026-09-21.json')));
 assert.equal(rate.status,'complete_no_all_width_rate_certificate_three_precise_obstructions');
 assert.equal(rate.new_physical_record_samples,0);assert.equal(rate.decoder_runs,0);
 const witness=rate.symbolic_recurrence_audit.local_state_counterexample;
 assert.equal(witness.left.full_state,79);assert.equal(witness.right.full_state,106);
 assert.equal(witness.same_full_charge,true);assert.equal(witness.different_selected_paths,true);
 assert.equal(rate.symbolic_recurrence_audit.W6_extensional_truth_table.evaluated,false);
 assert.equal(rate.symbolic_recurrence_audit.W6_extensional_truth_table.configurations,8388608);
 assert.deepEqual(rate.embedded_family_audit.map(x=>x.physical_majority_states_mapping_to_zero),[0,0,0]);
 assert.equal(rate.uniform_tail_audit.path_counts.at(-1).simple_paths,405841);
 assert.equal(rate.branch_matrix.uniform_fan_tail_upper_bound.outcome,'path_count_cutoff_is_valid_but_not_uniformly_summable');
 assert.equal(rate.decision.threshold_claim,'No threshold claim is promoted.');
 for(const [file,h] of Object.entries(rate.source_sha256))assert.equal(sha(path.join(ROOT,file)),h,file);
 const audit=JSON.parse(read(path.join(LAB,'results/midpoint-alternative-theorem-interface-audit-2026-09-21.json')));
 assert.equal(audit.status,'complete_no_hypothesis_complete_theorem_interface_selector_route_demoted');
 assert.equal(audit.new_physical_record_samples,0);assert.equal(audit.decoder_runs,0);
 assert.equal(audit.primary_sources_reviewed,9);
 assert(audit.applicability_matrix.every(x=>x.applicable===false));
 assert.equal(audit.exact_counterexamples_reused.length,3);
 assert.equal(audit.branch_matrix.random_cluster_and_disjoint_occurrence.outcome,'no_hypothesis_complete_posterior_balance_interface');
 assert.equal(audit.branch_matrix.planar_orientation_and_flow.outcome,'no_hypothesis_complete_restricted_logical_graph_interface');
 assert.equal(audit.branch_matrix.finite_width_spectral.outcome,'valid_only_for_a_fixed_strip_after_a_closed_state_is_found');
 assert.equal(audit.decision.outcome,'demote_selector_route_and_promote_decoder_independent_posterior_gap_question');
 assert.equal(audit.decision.threshold_claim,'No threshold claim is promoted.');
 for(const [file,h] of Object.entries(audit.source_sha256||{}))assert.equal(sha(path.join(ROOT,file)),h,file);
 const gap=JSON.parse(read(path.join(LAB,'results/posterior-gap-order-parameter-synthesis-2026-09-21.json')));
 assert.equal(gap.status,'complete_order_parameter_identity_existing_data_insufficient_go_boundary_acquisition');
 assert.equal(gap.new_physical_record_samples,0);assert.equal(gap.decoder_runs,0);assert.equal(gap.new_bootstrap_replicates,0);
 assert.equal(gap.existing_result_families_used,5);assert.equal(gap.existing_p030_square_rows.length,15);
 assert.equal(gap.order_parameter.correctability_equivalence,'R_L->0 if and only if G_L->infinity in physical-record probability');
 assert(gap.existing_p030_square_rows.every(x=>x.integrity.maximum_record_logistic_identity_error<1e-14));
 const gapQ90=gap.existing_p030_square_trajectories.find(x=>x.q===0.9),gapQ97=gap.existing_p030_square_trajectories.find(x=>x.q===0.97),gapQ1=gap.existing_p030_square_trajectories.find(x=>x.q===1);
 assert(Math.abs(gapQ90.Bayes_risk.at(-1)-0.2449550838571719)<1e-15);
 assert.equal(gapQ97.low_gap_probability_at_1.at(-1),0.23958333333333334);
 assert(Math.abs(gapQ1.median_abs_DeltaF.at(-1)-4.16313655079923)<1e-14);
 assert.equal(gap.go_no_go.decision,'GO_REGISTER_ONLY');assert.equal(gap.go_no_go.smallest_future_matrix.new_cells.length,5);
 assert.equal(gap.claim_boundary.selector_dependency,'none');
 for(const [file,h] of Object.entries(gap.source_sha256))assert.equal(sha(path.join(ROOT,file)),h,file);
 const preflight=JSON.parse(read(path.join(LAB,'results/posterior-gap-boundary-tail-preflight-2026-09-21.json')));
 assert.equal(preflight.status,'passed_exact_preflight_production_not_started');assert.equal(preflight.all_gates_pass,true);
 assert.equal(preflight.production_histories_generated,0);assert.equal(preflight.new_physical_record_samples,0);assert.equal(preflight.bootstrap_replicates,0);
 assert.equal(preflight.oracle_profile.candidate_transitions,43578135);assert.equal(preflight.oracle_profile.maximum_frontier,10);
 assert(preflight.resource_observation.total_runtime_seconds<600);assert(preflight.resource_observation.peak_memory_gib<8);
 assert(Object.values(preflight.resource_checks).every(Boolean));assert(Object.values(preflight.logical_relation_checks).every(Boolean));
 const acquisition=JSON.parse(read(path.join(LAB,'results/posterior-gap-boundary-tail-acquisition-progress-2026-09-21.json')));
 assert.equal(acquisition.status,'complete');assert.equal(acquisition.new_physical_records,2688);assert.equal(acquisition.cells.length,5);
 assert(acquisition.cells.every(x=>x.status==='complete'&&x.stop_reason==='precision_targets_passed'&&x.summary.precision_targets_pass));
 assert(Object.values(acquisition.integrity).every(Boolean));
 const tail=JSON.parse(read(path.join(LAB,'results/posterior-gap-boundary-tail-analysis-2026-09-21.json')));
 assert.equal(tail.status,'complete_finite_size_outward_gap_motion_no_rare_tail_takeover_asymptotic_class_unresolved');
 assert.equal(tail.matrix_cells,9);assert.equal(tail.new_physical_records,2688);assert.equal(tail.new_bootstrap_replicates,4000);
 assert(Object.values(tail.integrity).every(Boolean));assert(tail.trajectory_checks.every(x=>x.Bayes_risk_strictly_decreases&&x.C_L_1_strictly_decreases&&x.median_gap_strictly_increases&&x.lower_quartile_gap_strictly_increases&&x.B_L_1_L11_not_above_L7));
 assert.equal(tail.mechanism_assessment.rare_tail_control.finite_size_evidence,'not supported through L11');
 assert.equal(tail.decision.threshold_claim,'No threshold, critical q, crossing, exponent, universality or BKT claim is made.');
 assert.equal(meta.results.filter(x=>x.id==='posterior-gap-boundary-tail-matrix').length,1);
 const shots=path.join(ROOT,'.tmp/lab008-threshold-delivery');fs.mkdirSync(shots,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const page=await browser.newPage({viewport:{width:1500,height:1050}}),errors=[],surfaces=[];
 page.on('pageerror',e=>errors.push(String(e)));
 try{
  for(const [name,file,kind,expected] of [
   ['report','REPORT.md','report','outward gap motion'],
   ['threshold-wiki','wiki/decoding-thresholds.md','wiki','complete 3-by-3 analysis'],
   ['threshold-document','wiki/decoding-thresholds.md','document','The posterior quantity needed for a decoding transition'],
   ['current-user-document','wiki/complex-weights-and-cft.md','document','Current priority: decoding transitions and correction thresholds'],
   ['sector-document','wiki/sector-predictions.md','document','Current priority: decoding transitions and correction thresholds']]){
    const repo='labs/'+id+'/'+file,slug=path.basename(file,'.md');
    const url=kind==='report'?'/lab?id='+id:kind==='wiki'?'/lab-wiki?lab='+id+'&page='+slug:'/document?path='+encodeURIComponent(repo);
    if(kind==='document')assert.equal((await get('/api/documents/file?path='+encodeURIComponent(repo))).content,read(path.join(LAB,file)));
    if(kind==='wiki')assert.equal((await get('/api/labs/'+id+'/wiki?page='+slug)).content,read(path.join(LAB,file)));
    await page.goto(base+url);const sel=kind==='report'?'#lab-document':kind==='wiki'?'#local-wiki-document':'.project-document-preview';
    await page.waitForSelector(sel+' h1');await page.evaluate(()=>document.fonts.ready);
    const doc=page.locator(sel);assert((await doc.innerText()).includes(expected));
    assert.equal(await doc.locator('.katex-error').count(),0,name);
    assert.deepEqual(await doc.locator('.katex-display').evaluateAll(ns=>ns.filter(n=>n.scrollWidth>n.clientWidth+2).map(n=>n.textContent)),[],name);
    const links=await doc.locator('a[href]').evaluateAll(ns=>ns.map(n=>n.getAttribute('href')).filter(x=>x.startsWith('/')));
    for(const link of links)assert.equal((await page.request.get(base+link)).status(),200,link);
    if(kind==='report')assert(await doc.locator('img').evaluateAll(ns=>ns.every(n=>n.complete&&n.naturalWidth>0)));
    await page.screenshot({path:path.join(shots,name+'.png')});
    const panels=name==='report'?[['L008.22 Directed square midpoint and the threshold obstruction','report-result'],['L008.23 Boundary-tail matrix and Next question','boundary-tail-matrix']]:name==='threshold-document'?[
      ['Current rigorous threshold information','threshold-bounds'],
      ['The posterior quantity needed for a decoding transition','posterior-target'],
      ['Exact finite control and a rejected shortcut','exact-control'],
      ['Boundary-flux polynomial and the stability obstruction','polynomial-obstruction'],
      ['Exact transfer and why the direct interlacing induction fails','transfer-obstruction'],
      ['Direct path switching: valid local move, invalid global selector','switching-selector-obstruction'],
      ['Full switching graph: finite saturation, asymptotic capacity still open','fractional-switching-capacity'],
      ['Orientation-lattice audit: exact NMP, missing restricted theorem','orientation-lattice-nmp'],
      ['Why crossing plus NMP is still insufficient','minority-mass-obstruction'],
      ['Exact finite fiber imbalance and the averaged target','charge-fiber-balance'],
      ['Why two-copy overlap and local gluing do not yet close the average','averaged-balance-boundary'],
      ['Why collision-to-physical conversion is not dimension-free','collision-comparison-boundary'],
      ['Direct physical risk reduces to average selector multiplicity','direct-risk-reduction'],
      ['The second moment is an exact collision-pair count','selector-collision-matrix'],
      ['Why ordinary geodesic exchange does not cover the collisions','boundary-fan-exchange-gap'],
      ['The fan witness is finite-injective, but BK/Reimer has the wrong law','boundary-fan-tail-gap'],
      ['The physical strip keeps finite fan multiplicity, but selector memory is nonlocal','boundary-fan-strip-transfer'],
      ['The W=5 exact selector moment is feasible, but no rate follows','selector-automaton-feasibility'],
      ['The three all-width routes stop at different exact obstructions','selector-rate-obstructions'],
      ['No reviewed theorem closes the selector interface','alternative-theorem-interface-audit'],
      ['Posterior gap gives the selector-free order parameter','posterior-gap-order-parameter']]:[];
    for(const [title,shot] of panels){await doc.locator('h3,h4').filter({hasText:title}).evaluate(el=>el.scrollIntoView({block:'start'}));await page.screenshot({path:path.join(shots,shot+'.png')});}
    surfaces.push({name,url:base+url,file,sha256:sha(path.join(LAB,file)),local_links:links.length});
  }
  assert.deepEqual(errors,[]);
 }finally{await browser.close();}
 const files=['PLAN.md','REPORT.md','lab.json','wiki/index.md','wiki/decoding-thresholds.md','wiki/complex-weights-and-cft.md','wiki/sector-predictions.md',
 'scripts/check_square_midpoint.py','scripts/check_posterior_balance_polynomial.py','scripts/verify_threshold_delivery.cjs',
 'scripts/check_posterior_polynomial_closure.py','scripts/check_midpoint_switching_pairing.py','scripts/check_midpoint_fractional_switching.py',
 'scripts/audit_midpoint_all_size_matching_theorem.py','scripts/test_midpoint_all_size_matching_theorem.py',
 'scripts/audit_midpoint_minority_mass_lower_bound.py','scripts/test_midpoint_minority_mass_lower_bound.py',
 'scripts/audit_midpoint_charge_fiber_balance.py','scripts/test_midpoint_charge_fiber_balance.py',
 'scripts/audit_midpoint_averaged_charge_balance.py','scripts/test_midpoint_averaged_charge_balance.py',
 'scripts/audit_midpoint_charge_collision_comparison.py','scripts/test_midpoint_charge_collision_comparison.py',
 'scripts/audit_midpoint_direct_risk_renormalization.py','scripts/test_midpoint_direct_risk_renormalization.py',
 'scripts/audit_midpoint_selector_second_moment.py','scripts/test_midpoint_selector_second_moment.py',
 'scripts/audit_midpoint_shortest_selector_exchange.py','scripts/test_midpoint_shortest_selector_exchange.py',
 'scripts/audit_midpoint_boundary_fan_tail.py','scripts/test_midpoint_boundary_fan_tail.py',
 'scripts/audit_midpoint_boundary_fan_strip_transfer.py','scripts/test_midpoint_boundary_fan_strip_transfer.py',
 'scripts/audit_midpoint_selector_automaton_feasibility.py','scripts/test_midpoint_selector_automaton_feasibility.py',
 'scripts/audit_midpoint_selector_rate_certificate.py','scripts/test_midpoint_selector_rate_certificate.py',
 'scripts/synthesize_posterior_gap_order_parameter.py','scripts/preflight_posterior_gap_boundary_tail.py','scripts/acquire_posterior_gap_boundary_tail.py','scripts/analyze_posterior_gap_boundary_tail.py',
 'results/square-midpoint-thermodynamics-2026-09-20.json',
 'results/posterior-balance-polynomial-2026-09-20.json','results/posterior-polynomial-closure-2026-09-20.json',
 'results/midpoint-switching-pairing-2026-09-20.json',
 'results/midpoint-fractional-switching-2026-09-20.json',
 'results/midpoint-all-size-matching-theorem-2026-09-20.json',
 'results/midpoint-minority-mass-lower-bound-2026-09-20.json',
 'results/midpoint-charge-fiber-balance-theorem-2026-09-20.json',
 'results/midpoint-averaged-charge-balance-2026-09-20.json',
 'results/midpoint-charge-collision-comparison-2026-09-20.json',
 'results/midpoint-direct-risk-renormalization-2026-09-20.json',
 'results/midpoint-selector-second-moment-renormalization-2026-09-20.json',
 'results/midpoint-shortest-selector-geodesic-exchange-2026-09-20.json',
 'results/midpoint-boundary-fan-tail-2026-09-21.json',
 'results/midpoint-boundary-fan-strip-transfer-2026-09-21.json',
 'results/midpoint-selector-automaton-feasibility-2026-09-21.json',
 'results/midpoint-selector-rate-certificate-2026-09-21.json',
 'results/midpoint-alternative-theorem-interface-audit-2026-09-21.json',
 'results/posterior-gap-order-parameter-synthesis-2026-09-21.json','results/posterior-gap-boundary-tail-preflight-2026-09-21.json',
 'results/posterior-gap-boundary-tail-acquisition-progress-2026-09-21.json',
 'results/posterior-gap-boundary-tail-cells/square-L7-p30-q94-boundary-tail.json',
 'results/posterior-gap-boundary-tail-cells/square-L9-p30-q94-boundary-tail.json',
 'results/posterior-gap-boundary-tail-cells/square-L11-p30-q90-boundary-tail.json',
 'results/posterior-gap-boundary-tail-cells/square-L11-p30-q94-boundary-tail.json',
 'results/posterior-gap-boundary-tail-cells/square-L11-p30-q97-boundary-tail.json',
 'results/posterior-gap-boundary-tail-analysis-2026-09-21.json','figures/posterior-gap-boundary-tail-matrix.png',
 'manifests/square-midpoint-thermodynamics-2026-09-20.json','manifests/posterior-balance-2026-09-20.json',
 'manifests/posterior-polynomial-closure-2026-09-20.json','manifests/midpoint-switching-pairing-2026-09-20.json',
 'manifests/midpoint-fractional-switching-2026-09-20.json','manifests/midpoint-all-size-matching-theorem-2026-09-20.json',
 'manifests/midpoint-minority-mass-lower-bound-2026-09-20.json','manifests/midpoint-charge-fiber-balance-theorem-2026-09-20.json',
 'manifests/midpoint-averaged-charge-balance-2026-09-20.json','manifests/midpoint-charge-collision-comparison-2026-09-20.json',
 'manifests/midpoint-direct-risk-renormalization-2026-09-20.json',
 'manifests/midpoint-selector-second-moment-renormalization-2026-09-20.json',
 'manifests/midpoint-shortest-selector-geodesic-exchange-2026-09-20.json',
 'manifests/midpoint-boundary-fan-tail-2026-09-20.json',
 'manifests/midpoint-boundary-fan-strip-transfer-2026-09-21.json',
 'manifests/midpoint-selector-automaton-feasibility-2026-09-21.json',
 'manifests/midpoint-selector-rate-certificate-2026-09-21.json',
 'manifests/midpoint-alternative-theorem-interface-audit-2026-09-21.json',
 'manifests/posterior-gap-order-parameter-synthesis-2026-09-21.json',
 'manifests/posterior-gap-boundary-tail-acquisition-2026-09-21.json'];
 const out={status:'browser_verified_pending_visual_review',updated:new Date().toISOString(),surfaces,page_errors:errors,
  file_sha256:Object.fromEntries(files.map(f=>[f,sha(path.join(LAB,f))])),screenshots:path.relative(ROOT,shots),
  scope:'Decoder-independent transition observable after selector-route closure: the complete p=.30, q=.90,.94,.97, L=7,9,11 matrix shows pointwise-bootstrap-resolved risk/CDF decline and gap-quantile growth, while low-gap risk share does not increase. This favors finite-size outward typical-gap motion, weakens a persistent plateau and finds no rare-tail takeover through L11. The thermodynamic class remains unresolved; no threshold, critical q, exponent or BKT class is claimed.'};
 fs.writeFileSync(path.join(LAB,'results/decoding-thresholds-delivery-2026-09-20.json'),JSON.stringify(out,null,2)+'\n');
 console.log(JSON.stringify({status:out.status,surfaces:surfaces.map(x=>x.name),screenshots:out.screenshots}));
}
main().catch(e=>{console.error(e);process.exit(1);});
