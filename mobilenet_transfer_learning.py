"""
MobileNetV2 Transfer Learning for Disease Classification

Usage:
    python mobilenet_transfer_learning.py train
    python mobilenet_transfer_learning.py predict <image>
    python mobilenet_transfer_learning.py evaluate
"""

import os, sys, json, logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

# ── Paths (relative to this script, works from any cwd) ──
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR / "runs" / "disease_classifier"
DATASET_DIR = SCRIPT_DIR / "dataset" / "PlantVillage"
MODEL_SAVE_PATH = PROJECT_DIR / "best_model.pt"
CLASSES_PATH = PROJECT_DIR / "classes.json"

TRAINING_CONFIG = {
    "epochs": 1,
    "batch_size": 32,
    "learning_rate": 0.001,
    "img_size": 224,
    "num_workers": 2,
    "train_split": 0.8,
    "freeze_backbone": True,
    "unfreeze_epoch": 5,
}






def get_device():
    """Pick  available device: MPS -> CUDA -> CPU."""
    import torch
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def get_inference_transform():
    """Standard inference transform -- ImageNet normalization."""
    from torchvision import transforms
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])


def load_model(device=None):
    """
    Load saved .pt model. Returns (model, classes).
    Falls back to pretrained ImageNet MobileNetV2 if no trained model exists.
    """
    import torch
    from torchvision import models

    if device is None:
        device = get_device()

    if MODEL_SAVE_PATH.exists():
        ckpt = torch.load(str(MODEL_SAVE_PATH), map_location=device, weights_only=False)
        model = ckpt["model"]
        classes = ckpt["classes"]
        logger.info(f"Loaded trained model ({len(classes)} classes) from {MODEL_SAVE_PATH}")
    else:
        model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
        classes = None
        logger.info("No trained model found -- using pretrained ImageNet MobileNetV2")

    model = model.to(device)
    model.eval()
    return model, classes



# DATA TRANSFORMS & LOADERS (training only)


def get_data_transforms():
    from torchvision import transforms
    img_size = TRAINING_CONFIG["img_size"]
    mean, std = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]

    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(img_size, scale=(0.7, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.2),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])

    val_transform = transforms.Compose([
        transforms.Resize(img_size + 32),
        transforms.CenterCrop(img_size),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])

    return train_transform, val_transform


def create_dataloaders():
    from torchvision.datasets import ImageFolder
    from torch.utils.data import DataLoader, random_split

    train_transform, val_transform = get_data_transforms()
    full_dataset = ImageFolder(str(DATASET_DIR), transform=train_transform)

    train_size = int(TRAINING_CONFIG["train_split"] * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
    val_dataset.dataset.transform = val_transform

    train_loader = DataLoader(train_dataset, batch_size=TRAINING_CONFIG["batch_size"],
                              shuffle=True, num_workers=TRAINING_CONFIG["num_workers"])
    val_loader = DataLoader(val_dataset, batch_size=TRAINING_CONFIG["batch_size"],
                            shuffle=False, num_workers=TRAINING_CONFIG["num_workers"])

    classes = full_dataset.classes
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    with open(CLASSES_PATH, "w") as f:
        json.dump(classes, f, indent=2)

    logger.info(f"Dataset: {len(full_dataset)} images, {len(classes)} classes")
    logger.info(f"Train: {train_size} | Val: {val_size}")
    return train_loader, val_loader, classes



# MODEL CREATION (training only)


def create_model(num_classes: int, freeze_backbone: bool = True):
    import torch.nn as nn
    from torchvision import models

    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)

    if freeze_backbone:
        for param in model.features.parameters():
            param.requires_grad = False
        logger.info("Backbone FROZEN -- only training classifier head")

    in_features = model.classifier[1].in_features  # 1280
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, 512),
        nn.ReLU(),
        nn.BatchNorm1d(512),
        nn.Dropout(p=0.2),
        nn.Linear(512, num_classes),
    )

    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"Classifier: 1280 -> 512 -> {num_classes} | {trainable:,}/{total:,} params")
    return model



# TRAINING


def train_model():
    import torch
    import torch.nn as nn

    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    device = get_device()
    logger.info(f"Device: {device}")

    train_loader, val_loader, classes = create_dataloaders()
    num_classes = len(classes)
    model = create_model(num_classes, freeze_backbone=TRAINING_CONFIG["freeze_backbone"]).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=TRAINING_CONFIG["learning_rate"],
    )
    # reduces the learning rate when training stops improving.
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)

    best_val_acc = 0.0
    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}


    print(f"  TRAINING MobileNetV2 -- {num_classes} classes | {device}")
 

    for epoch in range(TRAINING_CONFIG["epochs"]):
        # Phase 2: unfreeze backbone
        if epoch == TRAINING_CONFIG["unfreeze_epoch"] and TRAINING_CONFIG["freeze_backbone"]:
            logger.info("UNFREEZING backbone -- full fine-tuning begins")
            for param in model.features.parameters():
                param.requires_grad = True
            optimizer = torch.optim.Adam([
                {"params": model.features.parameters(), "lr": TRAINING_CONFIG["learning_rate"] * 0.1},
                {"params": model.classifier.parameters(), "lr": TRAINING_CONFIG["learning_rate"]},
            ])

        # Train
        model.train()
        train_loss, train_correct, train_total = 0, 0, 0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            train_correct += predicted.eq(labels).sum().item()
            train_total += labels.size(0)

        # Validate
        model.eval()
        val_loss, val_correct, val_total = 0, 0, 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)
                _, predicted = outputs.max(1)
                val_correct += predicted.eq(labels).sum().item()
                val_total += labels.size(0)

        # Metrics
        train_acc = train_correct / max(train_total, 1) * 100
        val_acc = val_correct / max(val_total, 1) * 100
        avg_train_loss = train_loss / max(train_total, 1)
        avg_val_loss = val_loss / max(val_total, 1)

        history["train_loss"].append(avg_train_loss)
        history["val_loss"].append(avg_val_loss)
        history["train_acc"].append(train_acc)
        history["val_acc"].append(val_acc)
        scheduler.step(avg_val_loss)

        # Save best model 
        marker = ""
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            model.eval()
            torch.save({
                "model": model,
                "classes": classes,
                "num_classes": num_classes,
                "epoch": epoch,
                "val_acc": val_acc,
            }, str(MODEL_SAVE_PATH))
            model.train()
            marker = " <- BEST"

        lr = optimizer.param_groups[0]["lr"]
        print(f"  Epoch {epoch+1:2d}/{TRAINING_CONFIG['epochs']} | "
              f"Loss: {avg_train_loss:.4f}/{avg_val_loss:.4f} | "
              f"Acc: {train_acc:.1f}%/{val_acc:.1f}% | "
              f"LR: {lr:.6f}{marker}")

    print(f"\nBest val accuracy: {best_val_acc:.1f}% -> {MODEL_SAVE_PATH}")

    with open(PROJECT_DIR / "history.json", "w") as f:
        json.dump(history, f, indent=2)
    return MODEL_SAVE_PATH



# PREDICTION


def predict_image(image_path: str, top_k: int = 3):
    import torch
    from PIL import Image

    device = get_device()
    model, classes = load_model(device)
    transform = get_inference_transform()

    img = Image.open(image_path).convert("RGB")
    input_tensor = transform(img).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(input_tensor)
        probs = torch.nn.functional.softmax(outputs, dim=1)
        top_probs, top_indices = probs.topk(top_k)


    print(f"  CLASSIFICATION: {os.path.basename(image_path)}")


    predictions = []
    for i in range(top_k):
        idx = top_indices[0][i].item()
        prob = top_probs[0][i].item()
        name = classes[idx] if classes else f"ImageNet_class_{idx}"
        crop, disease = parse_class_name(name)
        print(f"  {name:<35} {prob:.1%}")
        predictions.append({"class": name, "crop": crop, "disease": disease,
                           "confidence": round(prob, 4)})
    return predictions


def parse_class_name(class_name: str) -> tuple:
    """Parse 'Tomato___Late_blight' into ('Tomato', 'Late_blight')."""
    if "___" in class_name:
        parts = class_name.split("___")
        return parts[0], parts[1]
    return class_name, "unknown"



# EVALUATION


def evaluate_model():
    import torch
    from torchvision import datasets

    device = get_device()
    model, classes = load_model(device)

    if classes is None:
        print("No trained model found. Train first.")
        return

    _, val_transform = get_data_transforms()
    val_dataset = datasets.ImageFolder(str(DATASET_DIR), transform=val_transform)
    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=32, shuffle=False)

    correct, total = 0, 0
    class_correct, class_total = {}, {}

    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
            for label, pred in zip(labels, predicted):
                cls = classes[label.item()]
                class_total[cls] = class_total.get(cls, 0) + 1
                if label == pred:
                    class_correct[cls] = class_correct.get(cls, 0) + 1

    print(f"\n{'=' * 60}")
    print(f"  EVALUATION RESULTS")
    print(f"{'=' * 60}")
    print(f"  Overall: {correct/max(total,1)*100:.1f}% ({correct}/{total})\n")
    print(f"  {'Class':<35} {'Accuracy':>10} {'Count':>8}")
    print(f"  {'-' * 55}")
    for cls in sorted(class_total.keys()):
        acc = class_correct.get(cls, 0) / class_total[cls] * 100
        print(f"  {cls:<35} {acc:>9.1f}% {class_total[cls]:>7}")



# FASTAPI SERVER


from fastapi import FastAPI, UploadFile, File, HTTPException

app = FastAPI(title="MobileNetV2 Disease Classifier", version="1.0.0")

_model_cache = {"model": None, "classes": None}


def get_model():
    """Cached model loader for FastAPI."""
    if _model_cache["model"] is None:
        try:
            import torch
            model, classes = load_model(torch.device("cpu"))
            _model_cache["model"] = model
            _model_cache["classes"] = classes
        except Exception as e:
            logger.error(f"Model load failed: {e}")
    return _model_cache["model"], _model_cache["classes"]


@app.post("/classify")
async def classify_image(file: UploadFile = File(...)):
    import torch
    from PIL import Image
    from io import BytesIO

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(400, "Empty file")

    model, classes = get_model()
    if model is None:
        return {"error": "Model unavailable"}

    transform = get_inference_transform()
    img = Image.open(BytesIO(content)).convert("RGB")
    tensor = transform(img).unsqueeze(0)

    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.nn.functional.softmax(outputs, dim=1)
        top_probs, top_idx = probs.topk(5)

    predictions = []
    for i in range(5):
        idx = top_idx[0][i].item()
        cls = classes[idx] if classes and idx < len(classes) else f"class_{idx}"
        crop, disease = parse_class_name(cls)
        predictions.append({
            "class": cls, "crop": crop, "disease": disease,
            "confidence": round(top_probs[0][i].item(), 4),
        })

    return {
        "filename": file.filename,
        "top_prediction": predictions[0],
        "is_healthy": predictions[0]["disease"].lower() == "healthy",
        "predictions": predictions,
    }


@app.get("/classes")
def list_classes():
    _, classes = get_model()
    return {"count": len(classes or []), "classes": classes or []}




if __name__ == "__main__":
  
    # img = "image path"
    train_model()   
    # # predict_image(img)
    # evaluate_model()