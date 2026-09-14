import torch.nn as nn

try:
    import pennylane as qml
except Exception:
    qml = None


class NMNISTTemporalQSNN(nn.Module):
    """Eight-qubit QSNN that sequentially reuploads ordered event-bin channels."""

    def __init__(self, n_qubits=8, temporal_steps=8, n_classes=10):
        super().__init__()
        if qml is None:
            raise ImportError("PennyLane is required. Install requirements.txt")
        if n_qubits != 8 or temporal_steps != 8:
            raise ValueError("The frozen N-MNIST baseline requires 8 qubits and 8 temporal steps.")
        self.n_qubits = n_qubits
        self.temporal_steps = temporal_steps
        device = qml.device("default.qubit", wires=n_qubits, shots=None)

        @qml.qnode(device, interface="torch", diff_method="backprop")
        def circuit(inputs, weights):
            for step in range(temporal_steps):
                for wire in range(n_qubits):
                    qml.RY(
                        3.141592653589793 * inputs[..., step * n_qubits + wire], wires=wire
                    )
                    qml.RY(weights[step, wire, 0], wires=wire)
                    qml.RZ(weights[step, wire, 1], wires=wire)
                for wire in range(n_qubits):
                    qml.CNOT(wires=[wire, (wire + 1) % n_qubits])
            local = [qml.expval(qml.PauliZ(wire)) for wire in range(n_qubits)]
            correlations = [
                qml.expval(qml.PauliZ(wire) @ qml.PauliZ((wire + 1) % n_qubits))
                for wire in range(n_qubits)
            ]
            return local + correlations

        self.qlayer = qml.qnn.TorchLayer(circuit, {"weights": (temporal_steps, n_qubits, 2)})
        self.head = nn.Linear(2 * n_qubits, n_classes)

    def forward(self, event_channels):
        flattened = event_channels.reshape(*event_channels.shape[:-2], -1)
        return self.head(self.qlayer(flattened))

    def trainable_parameter_count(self):
        return sum(parameter.numel() for parameter in self.parameters() if parameter.requires_grad)

    def circuit_depth(self):
        return self.temporal_steps * (3 + self.n_qubits)
