//! Public transport-DSL checks, including compatibility with all 120 v2 rows.

use vam_native::observer_synthesis::{
    apply_transport, compile_legacy_representation_transform, compile_transport, compose_transport,
    encoded_recurrences, enumerate_representation_family, verify_task_transport, FiniteDomainV1,
    TransportInformationClassV1, TransportOpV1, TransportTermV1,
};

#[test]
fn every_published_transform_has_identical_dsl_semantics() {
    let family = enumerate_representation_family().unwrap();
    for transform in &family.transforms {
        let compiled = compile_legacy_representation_transform(transform).unwrap();
        let dsl = apply_transport(&compiled, &[0, 1, 2, 3]).unwrap();
        let legacy = encoded_recurrences(transform)
            .unwrap()
            .into_iter()
            .map(|row| row.pulses())
            .collect::<Vec<_>>();
        assert_eq!(dsl, legacy);
        assert_eq!(
            compiled.information_class(),
            TransportInformationClassV1::Injection
        );
    }
}

#[test]
fn composition_binds_cost_and_loss_keeps_the_first_collision_witness() {
    let four = FiniteDomainV1::new("composition-four", 4).unwrap();
    let identity = compile_transport(&TransportTermV1 {
        source: four.clone(),
        target: four.clone(),
        op: TransportOpV1::Identity,
    })
    .unwrap();
    let composed = compose_transport(&identity, &identity).unwrap();
    assert_eq!(composed.image(), identity.image());
    assert_eq!(composed.cost(), 2);
    assert_ne!(composed.digest(), identity.digest());

    let swap = compile_transport(&TransportTermV1 {
        source: four.clone(),
        target: four.clone(),
        op: TransportOpV1::Relabel(vec![1, 0, 3, 2]),
    })
    .unwrap();
    let same_image_different_children = compose_transport(&swap, &swap).unwrap();
    assert_eq!(same_image_different_children.image(), composed.image());
    assert_eq!(same_image_different_children.cost(), composed.cost());
    assert_ne!(same_image_different_children.digest(), composed.digest());

    let sixty_four = FiniteDomainV1::new("composition-sixty-four", 64).unwrap();
    let wide = compile_transport(&TransportTermV1 {
        source: sixty_four.clone(),
        target: sixty_four,
        op: TransportOpV1::Identity,
    })
    .unwrap();
    assert_eq!(compose_transport(&wide, &wide).unwrap().image().len(), 64);

    let loss = compile_transport(&TransportTermV1 {
        source: four,
        target: FiniteDomainV1::new("composition-one", 1).unwrap(),
        op: TransportOpV1::Group(vec![0, 0, 0, 0]),
    })
    .unwrap();
    assert_eq!(loss.collision_count(), 3);
    assert_eq!(loss.first_collision(), Some((0, 1, 0)));
}

#[test]
fn information_loss_and_task_preservation_are_independent_facts() {
    let four = FiniteDomainV1::new("four-state-source", 4).unwrap();
    let two = FiniteDomainV1::new("two-state-target", 2).unwrap();
    let loss = compile_transport(&TransportTermV1 {
        source: four,
        target: two,
        op: TransportOpV1::Group(vec![0, 1, 1, 0]),
    })
    .unwrap();
    assert_eq!(loss.information_class(), TransportInformationClassV1::Loss);
    assert!(loss.collision_count() > 0);
    assert!(
        verify_task_transport(&loss, &[0, 1, 1, 0], &[0, 1])
            .unwrap()
            .commuting_square
    );
    assert!(!loss.licenses_round_trip());
}

#[test]
fn recursive_composition_binds_children_cost_depth_nodes_and_boundaries() {
    let four = FiniteDomainV1::new("compose-four", 4).unwrap();
    let eight = FiniteDomainV1::new("compose-eight", 8).unwrap();
    let term = TransportTermV1 {
        source: four.clone(),
        target: eight.clone(),
        op: TransportOpV1::Compose(vec![
            TransportTermV1 {
                source: four.clone(),
                target: four.clone(),
                op: TransportOpV1::Relabel(vec![1, 0, 3, 2]),
            },
            TransportTermV1 {
                source: four.clone(),
                target: eight.clone(),
                op: TransportOpV1::ShiftEmbed(2),
            },
        ]),
    };
    let compiled = compile_transport(&term).unwrap();
    assert_eq!(compiled.image(), &[3, 2, 5, 4]);
    assert_eq!(compiled.cost(), 2);
    assert_ne!(
        compiled.digest(),
        compile_transport(&TransportTermV1 {
            source: four.clone(),
            target: eight.clone(),
            op: TransportOpV1::CanonicalEncode(vec![3, 2, 5, 4]),
        })
        .unwrap()
        .digest()
    );

    let bad_boundary = TransportTermV1 {
        target: four.clone(),
        ..term.clone()
    };
    assert!(compile_transport(&bad_boundary).is_err());

    let leaf = TransportTermV1 {
        source: four.clone(),
        target: four.clone(),
        op: TransportOpV1::Identity,
    };
    let too_many = TransportTermV1 {
        source: four.clone(),
        target: four.clone(),
        op: TransportOpV1::Compose(vec![leaf.clone(); 32]),
    };
    assert!(compile_transport(&too_many).is_err());

    let mut deep = leaf;
    for _ in 0..16 {
        deep = TransportTermV1 {
            source: four.clone(),
            target: four.clone(),
            op: TransportOpV1::Compose(vec![
                deep,
                TransportTermV1 {
                    source: four.clone(),
                    target: four.clone(),
                    op: TransportOpV1::Identity,
                },
            ]),
        };
    }
    assert!(compile_transport(&deep).is_err());
}

#[test]
fn typed_primitive_tags_cannot_disguise_an_arbitrary_table() {
    let four = FiniteDomainV1::new("tag-four", 4).unwrap();
    let two = FiniteDomainV1::new("tag-two", 2).unwrap();
    let arbitrary_same_cardinality = vec![0, 0, 0, 0];
    assert!(compile_transport(&TransportTermV1 {
        source: four.clone(),
        target: four.clone(),
        op: TransportOpV1::Relabel(arbitrary_same_cardinality.clone()),
    })
    .is_err());
    assert!(compile_transport(&TransportTermV1 {
        source: four.clone(),
        target: four.clone(),
        op: TransportOpV1::Group(arbitrary_same_cardinality.clone()),
    })
    .is_err());
    let literal = compile_transport(&TransportTermV1 {
        source: four.clone(),
        target: four,
        op: TransportOpV1::CanonicalEncode(arbitrary_same_cardinality),
    })
    .unwrap();
    assert_eq!(literal.cost(), 5);

    assert!(compile_transport(&TransportTermV1 {
        source: FiniteDomainV1::new("tag-project-source", 4).unwrap(),
        target: two.clone(),
        op: TransportOpV1::Project(vec![0, 1, 0, 1]),
    })
    .is_err());
    assert!(compile_transport(&TransportTermV1 {
        source: FiniteDomainV1::new("tag-group-source", 4).unwrap(),
        target: two,
        op: TransportOpV1::Group(vec![0, 0, 0, 0]),
    })
    .is_err());
}
