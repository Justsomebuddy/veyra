/- Shared native constructor semantics mirrored by src/core/semantic_kernel.py. -/

structure VeyraRez where
  name : String
deriving DecidableEq, Repr

structure VeyraNod where
  residue : VeyraRez
  mark : String
deriving DecidableEq, Repr

structure VeyraTact where
  start : VeyraNod
  stop : VeyraNod
  mark : String
deriving DecidableEq, Repr

structure VeyraBreath where
  tacts : List VeyraTact
  anchor : Option VeyraNod := none
deriving DecidableEq, Repr

structure VeyraMode where
  breath : VeyraBreath
  observer : String
deriving DecidableEq, Repr

inductive VeyraResult (α : Type) where
  | ready : α → VeyraResult α
  | blocked : String → VeyraResult α
deriving DecidableEq, Repr

def node (label : String) : VeyraNod :=
  { residue := { name := label }, mark := label }

def contact (left right : String) : VeyraTact :=
  { start := node left, stop := node right, mark := "touch" }

def contiguous : List VeyraTact → Bool
  | [] => false
  | [_] => true
  | first :: second :: rest =>
      decide (first.stop = second.start) && contiguous (second :: rest)

def boundary : List VeyraTact → Option (VeyraNod × VeyraNod)
  | [] => none
  | first :: rest => some (first.start, (rest.getLastD first).stop)

def breathBoundary (item : VeyraBreath) : Option (VeyraNod × VeyraNod) :=
  match item.tacts, item.anchor with
  | [], some point => some (point, point)
  | [], none => none
  | run, _ => boundary run

def validBreath (item : VeyraBreath) : Bool :=
  match item.tacts, item.anchor with
  | [], some _ => true
  | [], none => false
  | run, _ => contiguous run

def silentBreath (point : String) : VeyraBreath :=
  { tacts := [], anchor := some (node point) }

def evalBreath (run : List VeyraTact) : VeyraResult VeyraBreath :=
  if contiguous run then .ready { tacts := run, anchor := none }
  else .blocked "non-contiguous-or-empty"

def evalModeBreath (item : VeyraBreath) : VeyraResult VeyraMode :=
  if validBreath item then
    match breathBoundary item with
    | none => .blocked "empty-breath"
    | some edge =>
        if edge.1 = edge.2 then
          .ready { breath := item, observer := "native-cycle" }
        else .blocked "open-breath"
  else .blocked "non-contiguous-or-empty"

def evalMode (run : List VeyraTact) : VeyraResult VeyraMode :=
  match evalBreath run with
  | .blocked reason => .blocked reason
  | .ready readyBreath => evalModeBreath readyBreath

inductive VeyraObserver where
  | kind
  | boundary
  | length
deriving DecidableEq, Repr

inductive VeyraResponse where
  | kind : String → VeyraResponse
  | edge : VeyraNod → VeyraNod → VeyraResponse
  | length : Nat → VeyraResponse
deriving DecidableEq, Repr

def observeMode : VeyraObserver → List VeyraTact → Option VeyraResponse
  | .kind, run =>
      match evalMode run with
      | .ready _ => some (.kind "mode")
      | .blocked _ => none
  | .boundary, run =>
      match evalMode run, boundary run with
      | .ready _, some edge => some (.edge edge.1 edge.2)
      | _, _ => none
  | .length, run =>
      match evalMode run with
      | .ready _ => some (.length run.length)
      | .blocked _ => none

def echoMode (observer : VeyraObserver)
    (left right : List VeyraTact) : VeyraResult Bool :=
  match observeMode observer left, observeMode observer right with
  | some x, some y => if x = y then .ready true else .blocked "echo mismatch"
  | _, _ => .blocked "observer-domain"

theorem THM_R4_001_empty_breath_blocks :
    evalBreath [] = .blocked "non-contiguous-or-empty" := by
  rfl

theorem THM_R4_002_closed_tact_is_mode (point : String) :
    evalMode [contact point point] =
      .ready { breath := { tacts := [contact point point] },
               observer := "native-cycle" } := by
  simp [evalMode, evalModeBreath, evalBreath, validBreath, breathBoundary,
        contiguous, boundary, contact, node]

theorem THM_R4_003_open_tact_blocks (left right : String)
    (different : left ≠ right) :
    evalMode [contact left right] = .blocked "open-breath" := by
  simp [evalMode, evalModeBreath, evalBreath, validBreath, breathBoundary,
        contiguous, boundary, contact, node, different]

theorem THM_R4_004_two_tact_cycle_is_mode (left right : String) :
    evalMode [contact left right, contact right left] =
      .ready { breath := { tacts := [contact left right, contact right left] },
               observer := "native-cycle" } := by
  simp [evalMode, evalModeBreath, evalBreath, validBreath, breathBoundary,
        contiguous, boundary, contact, node]

theorem THM_R4_005_kind_echoes_closed_modes
    (left right : List VeyraTact)
    (leftMode rightMode : VeyraMode)
    (leftReady : evalMode left = .ready leftMode)
    (rightReady : evalMode right = .ready rightMode) :
    echoMode .kind left right = .ready true := by
  simp [echoMode, observeMode, leftReady, rightReady]

theorem THM_R4_006_boundary_mismatch_blocks (left right : String)
    (different : left ≠ right) :
    echoMode .boundary [contact left left] [contact right right] =
      .blocked "echo mismatch" := by
  simp [echoMode, observeMode, evalMode, evalModeBreath, evalBreath,
        validBreath, breathBoundary, boundary, contiguous, contact, node, different]

theorem THM_R4_007_anchored_silence_is_mode (point : String) :
    evalModeBreath (silentBreath point) =
      .ready { breath := silentBreath point, observer := "native-cycle" } := by
  simp [evalModeBreath, silentBreath, validBreath, breathBoundary]


/-- A ready native mode exposes the exact number of tacts through the length observer. -/
theorem native_length_observes_ready_mode
    (run : List VeyraTact) (readyMode : VeyraMode)
    (ready : evalMode run = .ready readyMode) :
    observeMode .length run = some (.length run.length) := by
  simp [observeMode, ready]
