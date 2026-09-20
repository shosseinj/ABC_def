# Expected Inputs / Outputs

## Phase 1
Input:
`[5.1, 3.5, 1.4, 0.2]`

Output:
- shape `(4,)`
- all normalized values in `[0,1]`

## Phase 2
Input:
`x_norm=[0.2,0.5,0.8,1.0], T=100`

Expected:
`[80,50,20,0]`

## Phase 3
Input:
`t=[0,25,50,100], T=100`

Expected:
`theta=[0, pi/8, pi/4, pi/2]`

## Phase 4
Input:
batch shape `[B,4]`

Expected:
logits shape `[B,3]`

## Phase 8
Input:
`t=[20,40,60,80], epsilon=5`

Expected:
- same shape
- all in `[0,T]`
- max perturbation <= 5

## Phase 9
Identical quantum states:
- trace distance = 0
- fidelity = 1

## Phase 10
Timing-only perturbation:
- spike count difference = 0
- firing-rate difference = 0

## Phase 11
TEMP-DRIFT reference optimizer:
- same shape
- bounded perturbation
- tries to increase quantum drift under stealth penalty
