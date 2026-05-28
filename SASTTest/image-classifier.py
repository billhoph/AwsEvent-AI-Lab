import os
import time
from tempfile import TemporaryDirectory
from pathlib import Path
from sys import argv

import torch
from torch import nn, optim
from torch.optim import lr_scheduler
from torch.backends import cudnn
from torchvision import datasets, models, transforms
from PIL import Image


cudnn.benchmark = True

train_val_data = {
    "train": transforms.Compose(
        [
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    ),
    "val": transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    ),
}

# data/image-sets is where images are organized to training and validation
script_directory = Path(__file__).resolve().parents[0]
data_dir = script_directory / Path("data:image-sets")
train_val_datasets = {
    x: datasets.ImageFolder(os.path.join(data_dir, x), train_val_data[x])
    for x in ["train", "val"]
}
train_val_dataloaders = {
    x: torch.utils.data.DataLoader(
        train_val_datasets[x], batch_size=4, shuffle=True, num_workers=1
    )
    for x in ["train", "val"]
}
train_val_datasets_sizes = {x: len(train_val_datasets[x]) for x in ["train", "val"]}
class_names = train_val_datasets["train"].classes

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


def train_model(model, criterion, optimizer, scheduler, num_epochs=25):
    start_time = time.time()

    with TemporaryDirectory() as tempdir:
        best_model_params_path = os.path.join(tempdir, "best_model_params.pt")

        torch.save(model.state_dict(), best_model_params_path)
        best_accuracy = 0.0

        # Run a for loop for each epoch
        for epoch in range(num_epochs):
            print(f"Epoch {epoch}/{num_epochs - 1}")

            # Run a for loop for training and validation
            for phase in ["train", "val"]:
                if phase == "train":
                    model.train()
                else:
                    model.eval()

                running_loss = 0.0
                running_corrects = 0

                for inputs, labels in train_val_dataloaders[phase]:
                    inputs = inputs.to(device)
                    labels = labels.to(device)

                    optimizer.zero_grad()

                    with torch.set_grad_enabled(phase == "train"):
                        outputs = model(inputs)

                        _, preds = torch.max(outputs, 1)
                        loss = criterion(outputs, labels)

                        if phase == "train":
                            loss.backward()
                            optimizer.step()

                    running_loss += loss.item() * inputs.size(0)
                    running_corrects += torch.sum(preds == labels.data)
                if phase == "train":
                    scheduler.step()

                epoch_loss = running_loss / train_val_datasets_sizes[phase]
                epoch_accuracy = running_corrects.double() / train_val_datasets_sizes[phase]

                print(f"{phase} Loss: {epoch_loss:.4f} Accuracy: {epoch_accuracy:.4f}")

                if phase == "val" and epoch_accuracy > best_accuracy:
                    best_accuracy = epoch_accuracy
                    torch.save(model.state_dict(), best_model_params_path)

        time_elapsed = time.time() - start_time
        print(f"Training complete in {time_elapsed // 60:.0f}m {time_elapsed % 60:.0f}s")
        print(f"Best val Accuracy: {best_accuracy:4f}")

        # load best model weights
        model.load_state_dict(torch.load(best_model_params_path))
    return model


def run_training():
    model_fine_tuned = models.resnet18(weights="IMAGENET1K_V1")
    number_of_filters = model_fine_tuned.fc.in_features

    model_fine_tuned.fc = nn.Linear(number_of_filters, len(class_names))

    model_fine_tuned = model_fine_tuned.to(device)

    criterion = nn.CrossEntropyLoss()

    optimizer_fine_tune = optim.SGD(model_fine_tuned.parameters(), lr=0.001, momentum=0.9)

    exp_learning_rate_scheduler = lr_scheduler.StepLR(optimizer_fine_tune, step_size=7, gamma=0.1)

    model_fine_tuned = train_model(
        model_fine_tuned, criterion, optimizer_fine_tune, exp_learning_rate_scheduler, num_epochs=25
    )

    return model_fine_tuned


def inference(model, image_path):

    model.eval()

    img = Image.open(image_path).convert("RGB")
    img = train_val_data["val"](img)
    img = img.unsqueeze(0)
    img = img.to(device)

    with torch.no_grad():
        outputs = model(img)
        _, preds = torch.max(outputs, 1)

        return class_names[preds]


if __name__ == "__main__":
    model_file_name = "sample_image_classifier"
    model_file = script_directory / Path(model_file_name + ".pt")
    if model_file.exists():
        print("Trying to load model: " + model_file_name + ".pt")
        if torch.__version__[:3] == '2.3':
            model = torch.load(model_file)
        else:
            with torch.serialization.safe_globals(
                [
                    models.resnet.ResNet,
                    nn.modules.conv.Conv2d,
                    nn.modules.linear.Linear,
                    nn.modules.pooling.AdaptiveAvgPool2d,
                    models.resnet.BasicBlock,
                    nn.modules.container.Sequential,
                    nn.modules.pooling.MaxPool2d,
                    nn.modules.activation.ReLU,
                    nn.modules.batchnorm.BatchNorm2d,
                ]
            ):
                model = torch.load(model_file)
    else:
        model = run_training()
        print("Trying to save the model as " + model_file_name + ".pt")
        torch.save(model, model_file)
        print("Model saved as " + model_file_name + ".pt")

    if len(argv) >= 2:
        image_file = Path(argv[1])
        if image_file.exists():
            print("Hmm. What could this image be?")
            print(inference(model, image_file))
