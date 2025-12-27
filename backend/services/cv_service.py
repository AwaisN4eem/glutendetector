"""Computer Vision Service for food photo detection - STAR FEATURE!
Implements complete Digital Image Processing pipeline for academic project."""
import cv2
import numpy as np
import base64
import json
import re
import os
from PIL import Image
from typing import Dict, List, Any, Optional, Tuple
from transformers import AutoFeatureExtractor, AutoModelForImageClassification
import torch
from groq import Groq
from config import settings
try:
    from skimage.feature import hog, local_binary_pattern
    from skimage import exposure
    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False
    print("⚠️ scikit-image not available - HOG/LBP features will be skipped")

try:
    from skimage.metrics import structural_similarity as ssim_func
    SSIM_AVAILABLE = True
except ImportError:
    SSIM_AVAILABLE = False
    print("⚠️ skimage.metrics not available - SSIM will use fallback calculation")

class CVService:
    """Computer Vision service for food detection from photos
    Includes complete DIP pipeline: preprocessing, edge detection, segmentation, morphology, feature extraction"""
    
    def __init__(self):
        """Initialize CV models and preprocessing"""
        
        # Initialize Groq client for Vision LLM (primary - more accurate)
        self.groq_client = None
        if settings.GROQ_API_KEY:
            try:
                self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
                print("✅ Groq Vision API initialized (primary detector)")
            except Exception as e:
                print(f"⚠️ Could not initialize Groq: {e}")
        else:
            print("⚠️ GROQ_API_KEY not set - using fallback model")
        
        # Load pre-trained food detection model as fallback
        print("🔄 Loading food detection model...")
        try:
            self.feature_extractor = AutoFeatureExtractor.from_pretrained("nateraw/food")
            self.model = AutoModelForImageClassification.from_pretrained("nateraw/food")
            self.model.eval()
            print("✅ Food detection model loaded (fallback)")
        except Exception as e:
            print(f"⚠️ Could not load model: {e}")
            self.model = None
        
        # Setup DIP debug output directory
        if settings.DIP_DEBUG_MODE:
            os.makedirs(settings.DIP_DEBUG_OUTPUT_DIR, exist_ok=True)
            print(f"📁 DIP Debug mode enabled - outputs saved to: {settings.DIP_DEBUG_OUTPUT_DIR}")
        
        # Gluten risk mappings (will be enhanced with database)
        self.gluten_keywords = {
            # High risk (80-100) - Western foods
            "bread": 100, "toast": 100, "sandwich": 100, "baguette": 100,
            "pizza": 100, "pasta": 100, "spaghetti": 100, "noodles": 90,
            "bagel": 100, "croissant": 100, "muffin": 90, "donut": 90,
            "cake": 90, "cookie": 90, "pancake": 90, "waffle": 90,
            "burger": 85, "hot dog": 85, "pretzel": 100,
            
            # High risk (80-100) - Desi/South Asian foods (ALL contain wheat flour)
            "roti": 100, "chapati": 100, "chappati": 100, "chapathi": 100,
            "naan": 100, "paratha": 100, "parantha": 100, "parota": 100,
            "puri": 100, "poori": 100, "bhatura": 100, "bhatoora": 100,
            "kulcha": 100, "rumali roti": 100, "tandoori roti": 100,
            "laccha paratha": 100, "aloo paratha": 100, "gobi paratha": 100,
            "samosa": 90, "samosas": 90, "pakora": 85, "pakoras": 85,
            "bhaji": 85, "onion bhaji": 85, "bonda": 85,
            "kachori": 90, "kachoris": 90, "mathri": 90,
            "biryani": 30, "biryani with naan": 100, "biryani with roti": 100,
            
            # Medium risk (40-79)
            "cereal": 70, "granola": 60, "oatmeal": 50, "cracker": 90,
            "tortilla": 80, "wrap": 80, "dumpling": 85, "ramen": 90,
            "fried": 60, "breaded": 90, "coated": 70,
            
            # Low risk (0-39) - Desi/South Asian safe foods
            "rice": 5, "basmati rice": 5, "jeera rice": 5, "pulao": 5, "pulav": 5,
            "dal": 5, "daal": 5, "lentil": 5, "lentils": 5, "dal fry": 5,
            "curry": 5, "sabzi": 5, "vegetable curry": 5, "aloo gobi": 5,
            "raita": 5, "yogurt": 5, "dahi": 5, "lassi": 5,
            "chicken curry": 5, "mutton curry": 5, "fish curry": 5,
            "salad": 10, "kachumber": 5, "fruit": 5, "vegetable": 5,
            "meat": 10, "chicken": 10, "beef": 10, "fish": 10,
            "egg": 5, "anda": 5, "potato": 10, "aloo": 10,
            "corn": 5, "quinoa": 5, "milk": 5, "cheese": 10,
            "paneer": 10, "paneer curry": 10, "paneer tikka": 10
        }

        # Confidence handling
        self.min_confidence = 0.05  # keep low to avoid returning "unknown" repeatedly
    
    def detect_food(self, image_path: str, generate_dip_output: Optional[bool] = None) -> Dict[str, Any]:
        """
        Main food detection pipeline with complete DIP processing:
        1. Preprocessing (Color models, Enhancement, Filtering)
        2. Edge Detection & Segmentation
        3. Morphological Processing
        4. Feature Extraction (HOG, Color Histograms)
        5. Classification (Groq Vision API or ML model)
        6. Generate debug outputs if enabled
        """
        
        # Use settings default if not specified
        if generate_dip_output is None:
            generate_dip_output = settings.DIP_DEBUG_MODE
        
        # Read original image
        original_image = cv2.imread(image_path)
        if original_image is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Generate DIP pipeline outputs for academic report
        dip_results = {}
        adaptive_dip_results = {}
        
        if generate_dip_output:
            # NEW: Run adaptive DIP analysis FIRST (quality assessment & recommendations)
            # This runs before the full pipeline to analyze and recommend techniques
            try:
                print("🔬 Starting Adaptive DIP Analysis (Quality Assessment & Recommendations)...")
                
                # Extract base filename for output directory (same logic as main pipeline)
                from datetime import datetime
                base_filename = os.path.splitext(os.path.basename(image_path))[0]
                timestamp_pattern = r'^\d{8}_\d{6}_'
                if re.match(timestamp_pattern, base_filename):
                    name_part = re.sub(timestamp_pattern, '', base_filename)
                else:
                    name_part = base_filename
                sanitized_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', name_part)
                sanitized_filename = sanitized_filename[:50] if len(sanitized_filename) > 50 else sanitized_filename
                
                # Generate session_id (same pattern as main pipeline for consistency)
                session_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + sanitized_filename
                output_dir = os.path.join(settings.DIP_DEBUG_OUTPUT_DIR, session_id)
                os.makedirs(output_dir, exist_ok=True)
                
                # Run adaptive analysis
                adaptive_dip_results = self._run_adaptive_dip_analysis(
                    original_image, output_dir, base_filename
                )
                print(f"✅ Adaptive DIP Analysis Complete - Status: {adaptive_dip_results.get('status', 'unknown')}")
                
            except Exception as e:
                import traceback
                print(f"⚠️ Adaptive DIP analysis failed (non-critical): {e}")
                print(traceback.format_exc())
                adaptive_dip_results = {"status": "failed", "error": str(e)}
            
            try:
                # EXISTING: Run complete DIP pipeline (unchanged, continues as before)
                dip_results = self._run_complete_dip_pipeline(image_path, original_image)
                
                # Merge adaptive results into dip_results for backward compatibility
                if adaptive_dip_results.get("status") == "success":
                    dip_results["adaptive_analysis"] = adaptive_dip_results
            except Exception as e:
                import traceback
                print(f"⚠️ DIP pipeline failed (non-critical): {e}")
                print(traceback.format_exc())
                # Continue with detection even if DIP processing fails
                dip_results = {}
                # Still include adaptive results if available
                if adaptive_dip_results.get("status") == "success":
                    dip_results["adaptive_analysis"] = adaptive_dip_results
        
        # Actual detection (LLM/ML model)
        detected_foods = None
        
        # Try Groq Vision API first (more accurate)
        if self.groq_client:
            try:
                detected_foods = self._detect_foods_groq(image_path)
                if detected_foods and detected_foods[0]["name"] != "unknown":
                    # Post-process even Groq results to catch misdetections
                    # Order matters: rice detection first, then desi foods, then common foods
                    detected_foods = self._post_process_rice_detection(detected_foods, original_image)
                    detected_foods = self._post_process_desi_foods(detected_foods, original_image)
                    detected_foods = self._post_process_common_foods(detected_foods, original_image)
                    gluten_risk_score = self._calculate_gluten_risk(detected_foods)
                    primary_food = detected_foods[0]["name"]
                    return {
                        "detected_foods": detected_foods,
                        "primary_food": primary_food,
                        "gluten_risk_score": gluten_risk_score,
                        "dip_pipeline": dip_results if generate_dip_output else None
                    }
            except Exception as e:
                print(f"⚠️ Groq detection failed, using fallback: {e}")
        
        # Fallback to local ML model
        detected_foods = self._detect_foods_ml(original_image)
        
        # Post-process to improve detection accuracy (ALWAYS run these)
        detected_foods = self._post_process_rice_detection(detected_foods, original_image)
        detected_foods = self._post_process_desi_foods(detected_foods, original_image)
        detected_foods = self._post_process_common_foods(detected_foods, original_image)
        
        gluten_risk_score = self._calculate_gluten_risk(detected_foods)
        primary_food = detected_foods[0]["name"] if detected_foods else "Unknown"
        
        return {
            "detected_foods": detected_foods,
            "primary_food": primary_food,
            "gluten_risk_score": gluten_risk_score,
            "dip_pipeline": dip_results if generate_dip_output else None
        }
    
    def _run_complete_dip_pipeline(self, image_path: str, original_image: np.ndarray) -> Dict[str, Any]:
        """
        Complete Digital Image Processing pipeline for academic demonstration:
        1. Color Models & Enhancement
        2. Filtering (Linear/Nonlinear)
        3. Edge Detection
        4. Segmentation
        5. Morphological Processing
        6. Feature Extraction (HOG, Color Histograms, Moments)
        
        Returns dict with paths to all generated images
        """
        from datetime import datetime
        import re
        
        # Extract base filename from image path
        base_filename = os.path.splitext(os.path.basename(image_path))[0]
        
        # Check if filename already starts with timestamp pattern (YYYYMMDD_HHMMSS_)
        timestamp_pattern = r'^\d{8}_\d{6}_'
        if re.match(timestamp_pattern, base_filename):
            # Extract just the name part (remove timestamp prefix)
            name_part = re.sub(timestamp_pattern, '', base_filename)
        else:
            # Use full filename
            name_part = base_filename
        
        # Sanitize filename for folder name (remove special characters, keep alphanumeric, underscore, hyphen)
        sanitized_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', name_part)
        # Limit length to avoid path issues
        sanitized_filename = sanitized_filename[:50] if len(sanitized_filename) > 50 else sanitized_filename
        
        # Generate unique session ID using timestamp + image filename
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + sanitized_filename
        output_dir = os.path.join(settings.DIP_DEBUG_OUTPUT_DIR, session_id)
        os.makedirs(output_dir, exist_ok=True)
        results = {
            "session_id": session_id,
            "output_directory": output_dir,
            "images": {}
        }
        
        # ========== STEP 1: PREPROCESSING (Color Models & Enhancement) ==========
        print("🔬 DIP Step 1: Preprocessing (Color Models & Enhancement)")
        
        # 1.1: Original image (save for comparison)
        original_path = os.path.join(output_dir, f"{base_filename}_00_original.jpg")
        cv2.imwrite(original_path, original_image)
        results["images"]["original"] = original_path
        
        # 1.2: Convert to different color spaces
        # RGB (already in BGR format from OpenCV)
        rgb_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
        rgb_path = os.path.join(output_dir, f"{base_filename}_01_rgb.jpg")
        cv2.imwrite(rgb_path, cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR))
        results["images"]["rgb"] = rgb_path
        
        # LAB color space
        lab_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2LAB)
        lab_path = os.path.join(output_dir, f"{base_filename}_02_lab.jpg")
        cv2.imwrite(lab_path, lab_image)
        results["images"]["lab"] = lab_path
        
        # HSV color space
        hsv_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2HSV)
        hsv_path = os.path.join(output_dir, f"{base_filename}_03_hsv.jpg")
        cv2.imwrite(hsv_path, hsv_image)
        results["images"]["hsv"] = hsv_path
        
        # 1.3: Histogram Equalization (Global)
        gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
        hist_eq = cv2.equalizeHist(gray)
        hist_eq_path = os.path.join(output_dir, f"{base_filename}_04_histogram_equalized.jpg")
        cv2.imwrite(hist_eq_path, hist_eq)
        results["images"]["histogram_equalized"] = hist_eq_path
        
        # 1.4: CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l, a, b = cv2.split(lab_image)
        l_enhanced = clahe.apply(l)
        enhanced_lab = cv2.merge([l_enhanced, a, b])
        enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        clahe_path = os.path.join(output_dir, f"{base_filename}_05_clahe_enhanced.jpg")
        cv2.imwrite(clahe_path, enhanced_bgr)
        results["images"]["clahe_enhanced"] = clahe_path
        
        # 1.5: Before/After comparison
        before_after = np.hstack([original_image, enhanced_bgr])
        comparison_path = os.path.join(output_dir, f"{base_filename}_06_before_after_enhancement.jpg")
        cv2.imwrite(comparison_path, before_after)
        results["images"]["before_after_enhancement"] = comparison_path
        
        # ========== STEP 2: FILTERING (Linear & Nonlinear) ==========
        print("🔬 DIP Step 2: Filtering (Linear & Nonlinear)")
        
        # 2.1: Linear Filtering - Gaussian Blur
        gaussian = cv2.GaussianBlur(enhanced_bgr, (5, 5), 0)
        gaussian_path = os.path.join(output_dir, f"{base_filename}_07_gaussian_filter.jpg")
        cv2.imwrite(gaussian_path, gaussian)
        results["images"]["gaussian_filter"] = gaussian_path
        
        # 2.2: Linear Filtering - Mean Filter
        mean_filter = cv2.blur(enhanced_bgr, (5, 5))
        mean_path = os.path.join(output_dir, f"{base_filename}_08_mean_filter.jpg")
        cv2.imwrite(mean_path, mean_filter)
        results["images"]["mean_filter"] = mean_path
        
        # 2.3: Linear Filtering - Sharpening (Laplacian)
        kernel_sharpen = np.array([[-1, -1, -1],
                                   [-1,  9, -1],
                                   [-1, -1, -1]])
        sharpened = cv2.filter2D(enhanced_bgr, -1, kernel_sharpen)
        sharpen_path = os.path.join(output_dir, f"{base_filename}_09_sharpened.jpg")
        cv2.imwrite(sharpen_path, sharpened)
        results["images"]["sharpened"] = sharpen_path
        
        # 2.4: Nonlinear Filtering - Median Filter
        median = cv2.medianBlur(enhanced_bgr, 5)
        median_path = os.path.join(output_dir, f"{base_filename}_10_median_filter.jpg")
        cv2.imwrite(median_path, median)
        results["images"]["median_filter"] = median_path
        
        # 2.5: Nonlinear Filtering - Bilateral Filter (edge-preserving)
        bilateral = cv2.bilateralFilter(enhanced_bgr, 9, 75, 75)
        bilateral_path = os.path.join(output_dir, f"{base_filename}_11_bilateral_filter.jpg")
        cv2.imwrite(bilateral_path, bilateral)
        results["images"]["bilateral_filter"] = bilateral_path
        
        # 2.6: Nonlinear Filtering - Non-local Means Denoising
        denoised = cv2.fastNlMeansDenoisingColored(enhanced_bgr, None, 10, 10, 7, 21)
        denoised_path = os.path.join(output_dir, f"{base_filename}_12_denoised.jpg")
        cv2.imwrite(denoised_path, denoised)
        results["images"]["denoised"] = denoised_path
        
        # Use enhanced image for further processing
        processed_image = enhanced_bgr
        
        # ========== STEP 3: EDGE DETECTION ==========
        print("🔬 DIP Step 3: Edge Detection")
        
        gray_processed = cv2.cvtColor(processed_image, cv2.COLOR_BGR2GRAY)
        
        # 3.1: Canny Edge Detection
        canny_edges = cv2.Canny(gray_processed, 50, 150)
        canny_path = os.path.join(output_dir, f"{base_filename}_13_canny_edges.jpg")
        cv2.imwrite(canny_path, canny_edges)
        results["images"]["canny_edges"] = canny_path
        
        # 3.2: Sobel Edge Detection
        sobel_x = cv2.Sobel(gray_processed, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray_processed, cv2.CV_64F, 0, 1, ksize=3)
        sobel_combined = np.sqrt(sobel_x**2 + sobel_y**2)
        sobel_combined = np.uint8(255 * sobel_combined / np.max(sobel_combined))
        sobel_path = os.path.join(output_dir, f"{base_filename}_14_sobel_edges.jpg")
        cv2.imwrite(sobel_path, sobel_combined)
        results["images"]["sobel_edges"] = sobel_path
        
        # 3.3: Laplacian Edge Detection
        laplacian = cv2.Laplacian(gray_processed, cv2.CV_64F)
        laplacian = np.uint8(np.absolute(laplacian))
        laplacian_path = os.path.join(output_dir, f"{base_filename}_15_laplacian_edges.jpg")
        cv2.imwrite(laplacian_path, laplacian)
        results["images"]["laplacian_edges"] = laplacian_path
        
        # ========== STEP 4: SEGMENTATION ==========
        print("🔬 DIP Step 4: Image Segmentation")
        
        # 4.1: Otsu's Thresholding (Automatic threshold selection)
        _, otsu_binary = cv2.threshold(gray_processed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        otsu_path = os.path.join(output_dir, f"{base_filename}_16_otsu_segmentation.jpg")
        cv2.imwrite(otsu_path, otsu_binary)
        results["images"]["otsu_segmentation"] = otsu_path
        
        # 4.2: Adaptive Thresholding
        adaptive_thresh = cv2.adaptiveThreshold(
            gray_processed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        adaptive_path = os.path.join(output_dir, f"{base_filename}_17_adaptive_segmentation.jpg")
        cv2.imwrite(adaptive_path, adaptive_thresh)
        results["images"]["adaptive_segmentation"] = adaptive_path
        
        # 4.3: K-Means Color Segmentation
        data = processed_image.reshape((-1, 3))
        data = np.float32(data)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        k = 5  # Number of clusters
        _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        centers = np.uint8(centers)
        segmented_data = centers[labels.flatten()]
        kmeans_segmented = segmented_data.reshape(processed_image.shape)
        kmeans_path = os.path.join(output_dir, f"{base_filename}_18_kmeans_segmentation.jpg")
        cv2.imwrite(kmeans_path, kmeans_segmented)
        results["images"]["kmeans_segmentation"] = kmeans_path
        
        # 4.4: Original vs Segmented comparison
        original_vs_segmented = np.hstack([original_image, kmeans_segmented])
        orig_seg_path = os.path.join(output_dir, f"{base_filename}_19_original_vs_segmented.jpg")
        cv2.imwrite(orig_seg_path, original_vs_segmented)
        results["images"]["original_vs_segmented"] = orig_seg_path
        
        # Use Otsu binary for morphology
        binary_mask = otsu_binary
        
        # ========== STEP 5: MORPHOLOGICAL PROCESSING ==========
        print("🔬 DIP Step 5: Morphological Processing")
        
        # 5.1: Erosion
        kernel_morph = np.ones((5, 5), np.uint8)
        eroded = cv2.erode(binary_mask, kernel_morph, iterations=1)
        eroded_path = os.path.join(output_dir, f"{base_filename}_20_erosion.jpg")
        cv2.imwrite(eroded_path, eroded)
        results["images"]["erosion"] = eroded_path
        
        # 5.2: Dilation
        dilated = cv2.dilate(binary_mask, kernel_morph, iterations=1)
        dilated_path = os.path.join(output_dir, f"{base_filename}_21_dilation.jpg")
        cv2.imwrite(dilated_path, dilated)
        results["images"]["dilation"] = dilated_path
        
        # 5.3: Opening (Erosion followed by Dilation)
        opening = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel_morph)
        opening_path = os.path.join(output_dir, f"{base_filename}_22_opening.jpg")
        cv2.imwrite(opening_path, opening)
        results["images"]["opening"] = opening_path
        
        # 5.4: Closing (Dilation followed by Erosion)
        closing = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel_morph)
        closing_path = os.path.join(output_dir, f"{base_filename}_23_closing.jpg")
        cv2.imwrite(closing_path, closing)
        results["images"]["closing"] = closing_path
        
        # 5.5: Morphological Gradient
        gradient = cv2.morphologyEx(binary_mask, cv2.MORPH_GRADIENT, kernel_morph)
        gradient_path = os.path.join(output_dir, f"{base_filename}_24_morphological_gradient.jpg")
        cv2.imwrite(gradient_path, gradient)
        results["images"]["morphological_gradient"] = gradient_path
        
        # 5.6: Refined mask (using closing to fill holes)
        refined_mask = closing
        refined_path = os.path.join(output_dir, f"{base_filename}_25_morphology_refined.jpg")
        cv2.imwrite(refined_path, refined_mask)
        results["images"]["morphology_refined"] = refined_path
        
        # ========== STEP 6: FEATURE EXTRACTION ==========
        print("🔬 DIP Step 6: Feature Extraction (HOG, Color Histograms, Moments)")
        
        # 6.1: Color Histograms (R, G, B channels)
        color_hist_path = self._generate_color_histogram(processed_image, output_dir, base_filename)
        results["images"]["color_histogram"] = color_hist_path
        
        # 6.2: HOG (Histogram of Oriented Gradients) Features
        hog_path = self._generate_hog_features(gray_processed, output_dir, base_filename)
        results["images"]["hog_features"] = hog_path
        
        # 6.3: Local Binary Pattern (LBP) for texture
        lbp_path = self._generate_lbp_features(gray_processed, output_dir, base_filename)
        results["images"]["lbp_features"] = lbp_path
        
        # 6.4: Image Moments
        moments_path = self._generate_moments_visualization(binary_mask, output_dir, base_filename)
        results["images"]["moments"] = moments_path
        
        # ========== STEP 7: SIFT FEATURE EXTRACTION ==========
        print("🔬 DIP Step 7: SIFT Feature Extraction")
        
        # 7.1: SIFT Keypoints Detection
        sift = cv2.SIFT_create()
        keypoints, descriptors = sift.detectAndCompute(gray_processed, None)
        
        # Visualize keypoints on processed image
        sift_image = processed_image.copy()
        cv2.drawKeypoints(processed_image, keypoints, sift_image, 
                         flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
        sift_path = os.path.join(output_dir, f"{base_filename}_sift_keypoints.jpg")
        cv2.imwrite(sift_path, sift_image)
        results["images"]["sift_keypoints"] = sift_path
        
        # 7.2: SIFT Features Visualization
        sift_features_path = self._generate_sift_features_visualization(
            gray_processed, keypoints, output_dir, base_filename
        )
        results["images"]["sift_features"] = sift_features_path
        
        # Store SIFT statistics
        results["sift_stats"] = {
            "num_keypoints": len(keypoints),
            "descriptor_size": descriptors.shape[1] if descriptors is not None else 0
        }
        
        # ========== STEP 8: CORNER DETECTION ==========
        print("🔬 DIP Step 8: Corner Detection")
        
        # 8.1: Harris Corner Detection
        harris_response = cv2.cornerHarris(gray_processed, blockSize=2, ksize=3, k=0.04)
        harris_response = cv2.dilate(harris_response, None)
        harris_image = processed_image.copy()
        harris_image[harris_response > 0.01 * harris_response.max()] = [0, 0, 255]  # Red corners
        harris_path = os.path.join(output_dir, f"{base_filename}_harris_corner_detection.jpg")
        cv2.imwrite(harris_path, harris_image)
        results["images"]["harris_corners"] = harris_path
        
        # Count Harris corners
        harris_corners = np.sum(harris_response > 0.01 * harris_response.max())
        
        # 8.2: Shi-Tomasi Corner Detection
        corners = cv2.goodFeaturesToTrack(gray_processed, maxCorners=200, 
                                         qualityLevel=0.01, minDistance=10)
        shitomasi_image = processed_image.copy()
        if corners is not None:
            for corner in corners:
                x, y = corner.ravel()
                cv2.circle(shitomasi_image, (int(x), int(y)), 3, (0, 255, 0), -1)  # Green corners
        shitomasi_path = os.path.join(output_dir, f"{base_filename}_shi_tomasi_corner_detection.jpg")
        cv2.imwrite(shitomasi_path, shitomasi_image)
        results["images"]["shitomasi_corners"] = shitomasi_path
        
        # Store corner detection statistics
        results["corner_stats"] = {
            "harris_corners": int(harris_corners),
            "shi_tomasi_corners": len(corners) if corners is not None else 0
        }
        
        # ========== STEP 9: IMAGE COMPRESSION ANALYSIS ==========
        print("🔬 DIP Step 9: Image Compression Analysis")
        
        compression_paths = self._generate_compression_analysis(
            original_image, output_dir, base_filename
        )
        results["images"]["compression_comparison"] = compression_paths["comparison"]
        results["images"]["compression_graph"] = compression_paths["graph"]
        results["compression_stats"] = compression_paths["stats"]
        
        print(f"✅ DIP Pipeline Complete - {len(results['images'])} images generated in {output_dir}")
        
        return results
    
    def _generate_color_histogram(self, image: np.ndarray, output_dir: str, base_filename: str) -> str:
        """Generate and save color histogram visualization"""
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
        
        colors = ('b', 'g', 'r')
        plt.figure(figsize=(10, 6))
        for i, color in enumerate(colors):
            hist = cv2.calcHist([image], [i], None, [256], [0, 256])
            plt.plot(hist, color=color, label=f'{color.upper()} Channel')
        plt.xlabel('Pixel Intensity')
        plt.ylabel('Frequency')
        plt.title('Color Histogram (RGB Channels)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        hist_path = os.path.join(output_dir, f"{base_filename}_26_color_histogram.png")
        plt.savefig(hist_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return hist_path
    
    def _generate_hog_features(self, gray_image: np.ndarray, output_dir: str, base_filename: str) -> str:
        """Generate and visualize HOG (Histogram of Oriented Gradients) features"""
        if not SKIMAGE_AVAILABLE:
            # Fallback: Create a simple gradient visualization
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            # Compute gradients using OpenCV
            grad_x = cv2.Sobel(gray_image, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray_image, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            gradient_magnitude = np.uint8(255 * gradient_magnitude / np.max(gradient_magnitude))
            
            fig, axes = plt.subplots(1, 2, figsize=(12, 6))
            axes[0].imshow(gray_image, cmap='gray')
            axes[0].set_title('Original Image')
            axes[0].axis('off')
            
            axes[1].imshow(gradient_magnitude, cmap='hot')
            axes[1].set_title('Gradient Features (HOG Alternative)')
            axes[1].axis('off')
            
            plt.tight_layout()
            hog_path = os.path.join(output_dir, f"{base_filename}_27_hog_features.png")
            plt.savefig(hog_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return hog_path
        
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        # Resize for HOG computation (HOG works better on smaller images)
        resized = cv2.resize(gray_image, (128, 128))
        
        # Compute HOG features
        fd, hog_image = hog(
            resized, 
            orientations=9, 
            pixels_per_cell=(8, 8),
            cells_per_block=(2, 2), 
            visualize=True,
            feature_vector=False
        )
        
        # Normalize HOG image for visualization
        hog_image = exposure.rescale_intensity(hog_image, in_range=(0, 10))
        
        # Create visualization
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        axes[0].imshow(resized, cmap='gray')
        axes[0].set_title('Original Image (Resized)')
        axes[0].axis('off')
        
        axes[1].imshow(hog_image, cmap='hot')
        axes[1].set_title('HOG Features Visualization')
        axes[1].axis('off')
        
        plt.tight_layout()
        hog_path = os.path.join(output_dir, f"{base_filename}_27_hog_features.png")
        plt.savefig(hog_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return hog_path
    
    def _generate_lbp_features(self, gray_image: np.ndarray, output_dir: str, base_filename: str) -> str:
        """Generate Local Binary Pattern features for texture analysis"""
        if not SKIMAGE_AVAILABLE:
            # Fallback: Create texture visualization using OpenCV
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            # Use adaptive threshold as texture alternative
            texture = cv2.adaptiveThreshold(
                gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            fig, axes = plt.subplots(1, 2, figsize=(12, 6))
            axes[0].imshow(gray_image, cmap='gray')
            axes[0].set_title('Original Grayscale')
            axes[0].axis('off')
            
            axes[1].imshow(texture, cmap='viridis')
            axes[1].set_title('Texture Pattern (LBP Alternative)')
            axes[1].axis('off')
            
            plt.tight_layout()
            lbp_path = os.path.join(output_dir, f"{base_filename}_28_lbp_features.png")
            plt.savefig(lbp_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return lbp_path
        
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        # Compute LBP
        radius = 3
        n_points = 8 * radius
        lbp = local_binary_pattern(gray_image, n_points, radius, method='uniform')
        
        # Visualize
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        axes[0].imshow(gray_image, cmap='gray')
        axes[0].set_title('Original Grayscale')
        axes[0].axis('off')
        
        axes[1].imshow(lbp, cmap='viridis')
        axes[1].set_title('Local Binary Pattern (LBP)')
        axes[1].axis('off')
        
        plt.tight_layout()
        lbp_path = os.path.join(output_dir, f"{base_filename}_28_lbp_features.png")
        plt.savefig(lbp_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return lbp_path
    
    def _generate_moments_visualization(self, binary_mask: np.ndarray, output_dir: str, base_filename: str) -> str:
        """Generate image moments visualization"""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        # Calculate moments
        moments = cv2.moments(binary_mask)
        
        # Calculate centroid
        if moments["m00"] != 0:
            cx = int(moments["m10"] / moments["m00"])
            cy = int(moments["m01"] / moments["m00"])
        else:
            cx, cy = 0, 0
        
        # Visualize
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(binary_mask, cmap='gray')
        ax.plot(cx, cy, 'r+', markersize=20, markeredgewidth=3, label='Centroid')
        ax.set_title(f'Image Moments\nCentroid: ({cx}, {cy})\nArea: {moments["m00"]:.0f} pixels')
        ax.legend()
        ax.axis('off')
        
        moments_path = os.path.join(output_dir, f"{base_filename}_29_moments.png")
        plt.savefig(moments_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return moments_path
    
    def _generate_sift_features_visualization(self, gray_image: np.ndarray, keypoints: Any, 
                                             output_dir: str, base_filename: str) -> str:
        """
        Generate SIFT features visualization showing keypoint distribution
        Reference: Lowe, D. G. (2004). Distinctive image features from scale-invariant keypoints.
        """
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        # Create visualization
        fig, axes = plt.subplots(1, 2, figsize=(14, 7))
        
        # Plot 1: Original image with keypoints
        axes[0].imshow(gray_image, cmap='gray')
        for kp in keypoints[:100]:  # Show first 100 keypoints for clarity
            x, y = kp.pt
            size = kp.size
            angle = kp.angle
            axes[0].plot(x, y, 'ro', markersize=size/10, alpha=0.6)
        axes[0].set_title(f'SIFT Keypoints Visualization\nTotal Keypoints: {len(keypoints)}')
        axes[0].axis('off')
        
        # Plot 2: Keypoint strength distribution
        if keypoints:
            strengths = [kp.response for kp in keypoints]
            axes[1].hist(strengths, bins=50, color='skyblue', edgecolor='black', alpha=0.7)
            axes[1].set_xlabel('Keypoint Response Strength', fontweight='bold')
            axes[1].set_ylabel('Frequency', fontweight='bold')
            axes[1].set_title('SIFT Keypoint Strength Distribution')
            axes[1].grid(True, alpha=0.3)
            axes[1].axvline(np.mean(strengths), color='red', linestyle='--', 
                          label=f'Mean: {np.mean(strengths):.3f}')
            axes[1].legend()
        else:
            axes[1].text(0.5, 0.5, 'No keypoints detected', 
                        ha='center', va='center', transform=axes[1].transAxes)
            axes[1].axis('off')
        
        plt.tight_layout()
        sift_features_path = os.path.join(output_dir, f"{base_filename}_sift_features_visualization.png")
        plt.savefig(sift_features_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return sift_features_path
    
    def _generate_compression_analysis(self, image: np.ndarray, output_dir: str, base_filename: str) -> Dict[str, Any]:
        """
        Generate JPEG compression analysis with different quality levels
        Reference: Wallace, G. K. (1991). The JPEG still picture compression standard.
        """
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        # Get original file size (approximate)
        original_size_bytes = image.nbytes
        original_size_kb = original_size_bytes / 1024
        
        # Compression quality levels to test
        quality_levels = [100, 90, 70, 50, 30]
        compressed_sizes = []
        compression_ratios = []
        
        # Compress at different quality levels
        for quality in quality_levels:
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            result, encimg = cv2.imencode('.jpg', image, encode_param)
            if result:
                compressed_size = len(encimg)
                compressed_sizes.append(compressed_size / 1024)  # KB
                compression_ratios.append(original_size_bytes / compressed_size)
            else:
                compressed_sizes.append(original_size_kb)
                compression_ratios.append(1.0)
        
        # Create comparison image (side-by-side)
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        
        # Original image
        axes[0, 0].imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        axes[0, 0].set_title(f'Original\nSize: {original_size_kb:.1f} KB', fontweight='bold')
        axes[0, 0].axis('off')
        
        # Compressed versions
        for idx, quality in enumerate([90, 70, 50]):
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            result, encimg = cv2.imencode('.jpg', image, encode_param)
            if result:
                compressed_img = cv2.imdecode(encimg, cv2.IMREAD_COLOR)
                row = (idx + 1) // 3
                col = (idx + 1) % 3
                axes[row, col].imshow(cv2.cvtColor(compressed_img, cv2.COLOR_BGR2RGB))
                size_kb = compressed_sizes[quality_levels.index(quality)]
                ratio = compression_ratios[quality_levels.index(quality)]
                axes[row, col].set_title(f'Quality {quality}%\nSize: {size_kb:.1f} KB\nRatio: {ratio:.1f}:1', 
                                       fontweight='bold')
                axes[row, col].axis('off')
        
        # Remove unused subplot
        axes[1, 2].axis('off')
        
        plt.suptitle('JPEG Compression Quality Comparison', fontsize=16, fontweight='bold', y=0.98)
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        comparison_path = os.path.join(output_dir, f"{base_filename}_jpeg_compression_comparison.jpg")
        plt.savefig(comparison_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        # Create compression analysis graph
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Plot 1: File size vs quality
        ax1.plot(quality_levels, compressed_sizes, marker='o', linewidth=2, markersize=8, color='#4ECDC4')
        ax1.axhline(y=original_size_kb, color='red', linestyle='--', label='Original Size', linewidth=2)
        ax1.set_xlabel('JPEG Quality Level (%)', fontweight='bold')
        ax1.set_ylabel('File Size (KB)', fontweight='bold')
        ax1.set_title('File Size vs Compression Quality', fontweight='bold', pad=15)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        ax1.invert_xaxis()  # Lower quality = smaller file size
        
        # Plot 2: Compression ratio vs quality
        ax2.plot(quality_levels, compression_ratios, marker='s', linewidth=2, markersize=8, color='#95E1D3')
        ax2.set_xlabel('JPEG Quality Level (%)', fontweight='bold')
        ax2.set_ylabel('Compression Ratio', fontweight='bold')
        ax2.set_title('Compression Ratio vs Quality Level', fontweight='bold', pad=15)
        ax2.grid(True, alpha=0.3)
        ax2.invert_xaxis()
        
        # Add value labels
        for quality, ratio in zip(quality_levels, compression_ratios):
            ax2.text(quality, ratio, f'{ratio:.1f}x', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        graph_path = os.path.join(output_dir, f"{base_filename}_compression_analysis_graph.png")
        plt.savefig(graph_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        # Prepare statistics
        stats = {
            "original_size_kb": round(original_size_kb, 2),
            "quality_90_size_kb": round(compressed_sizes[quality_levels.index(90)], 2),
            "quality_90_ratio": round(compression_ratios[quality_levels.index(90)], 2),
            "quality_70_size_kb": round(compressed_sizes[quality_levels.index(70)], 2),
            "quality_70_ratio": round(compression_ratios[quality_levels.index(70)], 2),
            "quality_50_size_kb": round(compressed_sizes[quality_levels.index(50)], 2),
            "quality_50_ratio": round(compression_ratios[quality_levels.index(50)], 2)
        }
        
        return {
            "comparison": comparison_path,
            "graph": graph_path,
            "stats": stats
        }
    
    def _post_process_desi_foods(self, detected_foods: List[Dict[str, Any]], image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Post-process detection results to improve desi food recognition.
        Uses image analysis to detect flatbreads and match them to desi foods.
        """
        if not detected_foods:
            return detected_foods
        
        print(f"🔍 Post-processing detection: {detected_foods[0]['name'] if detected_foods else 'none'}")
        
        # Check if detected foods look like desi flatbreads based on image characteristics
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        
        # Analyze image for flatbread characteristics:
        # 1. Round/circular shapes
        # 2. Light brown/golden color
        # 3. Stacked appearance
        # 4. Charred spots (tawa marks)
        
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Look for golden/brown colors (typical of roti/naan)
        lower_brown = np.array([10, 50, 50])
        upper_brown = np.array([30, 255, 255])
        brown_mask = cv2.inRange(hsv, lower_brown, upper_brown)
        brown_pixels = np.sum(brown_mask > 0)
        brown_ratio = brown_pixels / (h * w)
        
        # Look for circular shapes (contours)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        circular_shapes = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > (h * w * 0.05):  # Significant size
                perimeter = cv2.arcLength(contour, True)
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    if circularity > 0.7:  # Close to circle
                        circular_shapes += 1
        
        # Check if this looks like a flatbread (more lenient thresholds)
        is_flatbread = (
            brown_ratio > 0.15 and  # Significant brown/golden color (lowered from 0.2)
            (circular_shapes >= 1 or brown_ratio > 0.25) and  # Has circular shapes OR high brown ratio
            h > 100 and w > 100  # Reasonable image size (lowered from 200)
        )
        
        # If it looks like a flatbread but wasn't detected as one
        primary_name = detected_foods[0]["name"].lower() if detected_foods else ""
        
        # Common misdetections that should be desi foods
        desi_flatbread_keywords = ["roti", "chapati", "naan", "paratha", "puri", "flatbread", "bread", "tortilla"]
        desi_snack_keywords = ["samosa", "samosas", "pakora", "pakoras", "kachori", "kachoris", "bhaji", "bonda", "mathri"]
        western_dessert_keywords = ["macaron", "macarons", "cake", "cookie", "pastry", "dessert", "pie", "muffin", "donut"]
        
        # Check if already detected as a desi snack - DO NOT override these
        is_desi_snack = any(keyword in primary_name for keyword in desi_snack_keywords)
        if is_desi_snack:
            # Already correctly detected as desi snack, don't change it
            print(f"✅ Correctly detected as desi snack: {primary_name}")
            return detected_foods
        
        # Check for flatness (flatbreads are thin/flat, snacks are usually thicker/3D)
        # Calculate aspect ratio and thickness indicators
        aspect_ratio = max(h, w) / min(h, w) if min(h, w) > 0 else 1.0
        
        # More specific flatbread detection: needs to be flat AND brown
        # Flatbreads are typically wider than they are thick, and have uniform brown color
        is_actually_flatbread = (
            is_flatbread and
            aspect_ratio > 1.2 and  # Not too square (flatbreads are usually wider)
            not is_desi_snack  # Definitely not a snack
        )
        
        # More aggressive: If detected as western dessert OR if image clearly looks like flatbread
        should_correct = (
            (is_actually_flatbread and any(keyword in primary_name for keyword in western_dessert_keywords)) or
            (is_actually_flatbread and brown_ratio > 0.3 and not any(keyword in primary_name for keyword in desi_flatbread_keywords) and not is_desi_snack)
        )
        
        if should_correct:
            # Replace with desi flatbread detection
            # Determine which type based on characteristics
            if brown_ratio > 0.35 and circular_shapes >= 2:
                # Likely stacked rotis/chapatis
                desi_food = "roti"
                confidence = max(0.85, detected_foods[0].get("confidence", 0.5))  # Keep original confidence if higher
            elif brown_ratio > 0.25 and circular_shapes >= 1:
                # Could be naan or paratha
                desi_food = "naan"
                confidence = max(0.75, detected_foods[0].get("confidence", 0.5))
            elif brown_ratio > 0.2:
                # Likely chapati
                desi_food = "chapati"
                confidence = max(0.70, detected_foods[0].get("confidence", 0.5))
            else:
                # Default to roti if uncertain
                desi_food = "roti"
                confidence = max(0.65, detected_foods[0].get("confidence", 0.5))
            
            # Replace the primary detection
            detected_foods[0] = {
                "name": desi_food,
                "confidence": confidence,
                "gluten_risk": self._get_gluten_risk_for_food(desi_food)
            }
            
            print(f"🔄 Post-processed: '{primary_name}' → '{desi_food}' (flatbread detected, brown_ratio={brown_ratio:.2f}, circles={circular_shapes})")
        
        return detected_foods
    
    def _post_process_rice_detection(self, detected_foods: List[Dict[str, Any]], image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Post-process detection results to distinguish between different rice types:
        - Boiled/White Rice: Plain white rice, no vegetables, no fried appearance
        - Fried Rice: Has vegetables, darker colors, fried appearance
        - Biryani: Has meat/spices, richer colors, distinct layers
        
        Uses image analysis to verify and correct rice type detection.
        """
        if not detected_foods:
            return detected_foods
        
        primary_name = detected_foods[0]["name"].lower() if detected_foods else ""
        
        # Check if detection includes rice-related terms
        rice_keywords = ["rice", "fried rice", "fried_rice", "boiled rice", "white rice", 
                        "biryani", "biryani rice", "pulao", "pilaf", "pulav"]
        
        if not any(keyword in primary_name for keyword in rice_keywords):
            return detected_foods  # Not rice-related, no processing needed
        
        print(f"🔍 Post-processing rice detection: {primary_name}")
        
        # Analyze image characteristics
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        
        # 1. Check for vegetables/colorful ingredients (fried rice/biryani indicator)
        # Look for green, orange, red colors (vegetables)
        green_mask = cv2.inRange(hsv, np.array([40, 50, 50]), np.array([80, 255, 255]))
        orange_mask = cv2.inRange(hsv, np.array([10, 100, 100]), np.array([25, 255, 255]))
        red_mask = cv2.inRange(hsv, np.array([0, 100, 100]), np.array([10, 255, 255]))
        
        vegetable_pixels = np.sum(green_mask > 0) + np.sum(orange_mask > 0) + np.sum(red_mask > 0)
        vegetable_ratio = vegetable_pixels / (h * w)
        
        # 2. Check for color diversity (fried rice has more colors)
        # Calculate color variance - fried rice has higher variance
        color_variance = np.var(image.reshape(-1, 3), axis=0)
        avg_color_variance = np.mean(color_variance)
        
        # 3. Check for white/light colors dominance (boiled rice is mostly white)
        white_mask = cv2.inRange(hsv, np.array([0, 0, 200]), np.array([180, 30, 255]))
        white_pixels = np.sum(white_mask > 0)
        white_ratio = white_pixels / (h * w)
        
        # 4. Check for darker/brown colors (fried rice has darker appearance)
        brown_dark_mask = cv2.inRange(hsv, np.array([10, 50, 20]), np.array([30, 255, 180]))
        dark_pixels = np.sum(brown_dark_mask > 0)
        dark_ratio = dark_pixels / (h * w)
        
        # Decision logic with improved thresholds
        # Boiled/White rice: very high white ratio, very low vegetable ratio, low variance
        is_boiled_white_rice = (
            white_ratio > 0.6 and  # Mostly white (increased threshold)
            vegetable_ratio < 0.02 and  # No vegetables (stricter)
            avg_color_variance < 400 and  # Low color variance (uniform white)
            dark_ratio < 0.15  # Not much dark colors
        )
        
        # Biryani: rich colors, high variance, usually has more vegetables/spices
        is_biryani = (
            (vegetable_ratio > 0.08 and avg_color_variance > 700) or  # Rich colors with vegetables
            (dark_ratio > 0.25 and vegetable_ratio > 0.05) or  # Very dark with vegetables (spices/meat)
            (avg_color_variance > 800 and white_ratio < 0.3)  # Very high variance, not white
        )
        
        # Fried rice: has vegetables but not as rich as biryani
        is_fried_rice = (
            (vegetable_ratio > 0.04 and white_ratio < 0.5) or  # Has vegetables, not mostly white
            (avg_color_variance > 450 and dark_ratio > 0.12 and vegetable_ratio > 0.02) or  # Moderate variance with some vegetables
            (white_ratio < 0.45 and vegetable_ratio > 0.03)  # Not mostly white + has vegetables
        )
        
        # Correct the detection based on image analysis
        corrected_name = primary_name
        confidence = detected_foods[0].get("confidence", 0.7)
        
        if "fried" in primary_name or "fried_rice" in primary_name:
            if is_boiled_white_rice:
                # Was detected as fried rice but looks like boiled rice
                corrected_name = "rice"
                confidence = max(0.85, confidence)
                print(f"🔄 Corrected: '{primary_name}' → '{corrected_name}' (no vegetables, mostly white, low color variance)")
            elif is_biryani:
                corrected_name = "biryani"
                confidence = max(0.8, confidence)
                print(f"🔄 Corrected: '{primary_name}' → '{corrected_name}' (rich colors, high vegetable ratio)")
        elif "biryani" in primary_name:
            if is_boiled_white_rice:
                corrected_name = "rice"
                confidence = max(0.85, confidence)
                print(f"🔄 Corrected: '{primary_name}' → '{corrected_name}' (plain white rice detected)")
            elif is_fried_rice and not is_biryani:
                corrected_name = "fried rice"
                confidence = max(0.75, confidence)
                print(f"🔄 Corrected: '{primary_name}' → '{corrected_name}' (looks like fried rice, not biryani)")
        elif "rice" in primary_name and "fried" not in primary_name and "biryani" not in primary_name:
            # Plain rice detected - verify it's not fried rice
            if is_fried_rice:
                corrected_name = "fried rice"
                confidence = max(0.8, confidence)
                print(f"🔄 Corrected: '{primary_name}' → '{corrected_name}' (vegetables detected, high color variance)")
            elif is_biryani:
                corrected_name = "biryani"
                confidence = max(0.75, confidence)
                print(f"🔄 Corrected: '{primary_name}' → '{corrected_name}' (rich colors indicate biryani)")
            # If is_boiled_white_rice, keep as "rice" (correct detection)
        
        # Update the detection result if corrected
        if corrected_name != primary_name:
            detected_foods[0] = {
                "name": corrected_name,
                "confidence": confidence,
                "gluten_risk": self._get_gluten_risk_for_food(corrected_name)
            }
            print(f"✅ Final detection: {corrected_name} (confidence: {confidence:.2f})")
        else:
            print(f"✅ Detection confirmed: {primary_name} (confidence: {confidence:.2f})")
        
        return detected_foods
    
    def _post_process_common_foods(self, detected_foods: List[Dict[str, Any]], image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Post-process detection for common food misdetections.
        Fixes common issues with similar-looking foods.
        """
        if not detected_foods:
            return detected_foods
        
        primary_name = detected_foods[0]["name"].lower() if detected_foods else ""
        print(f"🔍 Post-processing common foods: {primary_name}")
        
        # Convert to HSV for color analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        
        # Common misdetection patterns
        corrections = {}
        
        # 1. Pasta vs Noodles vs Rice
        if "pasta" in primary_name or "noodle" in primary_name:
            # Check if it's actually rice (white, in a bowl, no sauce)
            white_mask = cv2.inRange(hsv, np.array([0, 0, 200]), np.array([180, 30, 255]))
            white_ratio = np.sum(white_mask > 0) / (h * w)
            
            # Check for sauce (red/orange colors typical of pasta sauce)
            red_mask = cv2.inRange(hsv, np.array([0, 100, 100]), np.array([10, 255, 255]))
            red_ratio = np.sum(red_mask > 0) / (h * w)
            
            if white_ratio > 0.5 and red_ratio < 0.05:
                # Looks like plain rice, not pasta
                corrections[primary_name] = "rice"
        
        # 2. Cake vs Bread vs Flatbread
        if "cake" in primary_name:
            # Check for frosting (sweet toppings typically have high saturation)
            high_sat_mask = cv2.inRange(hsv, np.array([0, 150, 0]), np.array([180, 255, 255]))
            high_sat_ratio = np.sum(high_sat_mask > 0) / (h * w)
            
            if high_sat_ratio < 0.2:
                # Low saturation, likely bread or flatbread, not cake
                # Check if it's a flatbread (golden/brown)
                brown_mask = cv2.inRange(hsv, np.array([10, 50, 50]), np.array([30, 255, 255]))
                brown_ratio = np.sum(brown_mask > 0) / (h * w)
                
                if brown_ratio > 0.2:
                    corrections[primary_name] = "roti"  # Likely flatbread
                else:
                    corrections[primary_name] = "bread"
        
        # 3. Salad vs Curry vs Vegetables
        if "salad" in primary_name:
            # Check for creamy/curry-like appearance (lower brightness, more saturated)
            mean_brightness = np.mean(hsv[:, :, 2])
            mean_saturation = np.mean(hsv[:, :, 1])
            
            if mean_brightness < 120 and mean_saturation > 80:
                # Looks like curry, not salad
                corrections[primary_name] = "curry"
        
        # 4. Cookie vs Samosa
        if "cookie" in primary_name:
            # Check for triangular shape (samosa is triangular)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > (h * w * 0.05):
                    # Check if it's triangular
                    approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
                    if len(approx) == 3:
                        corrections[primary_name] = "samosa"
                        break
        
        # Apply corrections
        if corrections:
            corrected_name = corrections.get(primary_name, primary_name)
            if corrected_name != primary_name:
                detected_foods[0] = {
                    "name": corrected_name,
                    "confidence": max(0.75, detected_foods[0].get("confidence", 0.7)),
                    "gluten_risk": self._get_gluten_risk_for_food(corrected_name)
                }
                print(f"🔄 Common food correction: '{primary_name}' → '{corrected_name}'")
        
        return detected_foods
    
    def _detect_foods_groq(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Detect foods using Groq Vision LLM (Llama 3.2 Vision) - highly accurate
        """
        # Read and encode image as base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Determine image type
        ext = image_path.lower().split(".")[-1]
        mime_type = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
        
        # Call Groq Vision API
        response = self.groq_client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": """Analyze this food image. Identify ALL foods visible.
For each food, respond in this exact JSON format:
{"foods": [{"name": "food name", "confidence": 0.95}]}

CRITICAL: Look for DESI/SOUTH ASIAN foods FIRST:
- Flatbreads: roti, chapati, naan, paratha, puri, bhatura, kulcha (NOT macarons, cookies, or cakes!)
- If you see round, flat, golden-brown breads stacked or on a plate, it's likely ROTI or CHAPATI
- If you see leavened, puffy flatbread, it's likely NAAN
- If you see layered/flaky flatbread, it's likely PARATHA
- Snacks: samosa (triangular fried pastry with filling), pakora (fried vegetable fritters), kachori (round fried snack), bhaji (fried vegetables)
- IMPORTANT: SAMOSA is a TRIANGULAR fried pastry with filling - NOT a flatbread! It has a distinct triangular shape and is thicker than flatbreads
- Main dishes: biryani, pulao, dal, curry
- Sides: raita, dahi, lassi

CRITICAL RICE DETECTION RULES:
- BOILED/WHITE RICE: Plain white rice in a bowl, no vegetables, no fried appearance, just white rice grains. Use "rice" or "white rice" or "boiled rice"
- FRIED RICE: Has vegetables (carrots, peas, onions), darker colors, fried appearance, mixed ingredients. Use "fried rice"
- BIRYANI: Has meat, spices, distinct layers, richer colors. Use "biryani"
- PULAO/PILAF: Has some vegetables but not as many as fried rice, lighter than biryani. Use "pulao" or "pilaf"
- DO NOT confuse plain white boiled rice with fried rice! If it's just white rice grains with no other ingredients, it's "rice" or "white rice", NOT "fried rice"

Rules:
- Use simple, common food names (e.g., "bread", "pizza", "salad", "roti", "naan", "paratha", "rice", "fried rice")
- DO NOT confuse roti/chapati with macarons, cookies, or cakes - roti is flatbread, not dessert
- DO NOT confuse plain white rice with fried rice - check for vegetables and fried appearance
- Confidence should be 0.0-1.0 based on how certain you are
- List the most prominent food first
- Be specific (e.g., "roti" or "naan" not just "bread", "rice" not "fried rice" if it's plain white rice)
- If you see flatbreads, identify if it's roti, naan, paratha, or chapati
- If you see fried snacks, identify if it's samosa (triangular), pakora (irregular fritters), or kachori (round)
- DO NOT confuse SAMOSA (triangular fried pastry) with CHAPATI (flat round bread) - they are completely different!
- Only return the JSON, nothing else"""
                        }
                    ]
                }
            ],
            max_tokens=300,
            temperature=0.1
        )
        
        # Parse response
        content = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            foods = data.get("foods", [])
            
            detected_foods = []
            for food in foods:
                name = food.get("name", "unknown").lower()
                confidence = float(food.get("confidence", 0.8))
                gluten_risk = self._get_gluten_risk_for_food(name)
                detected_foods.append({
                    "name": name,
                    "confidence": round(confidence, 3),
                    "gluten_risk": gluten_risk
                })
            
            if detected_foods:
                return detected_foods
        
        return [{"name": "unknown", "confidence": 0.0, "gluten_risk": 0}]
    
    def _preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Classical image processing techniques for enhancement:
        - CLAHE (Contrast Limited Adaptive Histogram Equalization)
        - Sharpening (Laplacian)
        - Noise reduction
        """
        
        # Read image
        img = cv2.imread(image_path)
        
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Convert to LAB color space for better processing
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel (contrast enhancement)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)
        
        # Merge back
        enhanced_lab = cv2.merge([l_enhanced, a, b])
        enhanced_img = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        # Apply sharpening (Laplacian)
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(enhanced_img, -1, kernel)
        
        # Reduce noise (Non-local means denoising)
        denoised = cv2.fastNlMeansDenoisingColored(sharpened, None, 10, 10, 7, 21)
        
        return denoised
    
    def _detect_foods_ml(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect foods using pre-trained ML model
        """
        if self.model is None:
            # Fallback: Return dummy result
            return [{"name": "food item", "confidence": 0.5, "gluten_risk": 50}]
        
        try:
            # Convert to PIL Image
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            
            # Extract features
            inputs = self.feature_extractor(pil_image, return_tensors="pt")
            
            # Run inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
            
            # Get top predictions
            probs = torch.nn.functional.softmax(logits, dim=-1)
            top_probs, top_indices = torch.topk(probs, k=5)
            
            # Map to food names and gluten risk
            detected_foods = []
            for rank, (prob, idx) in enumerate(zip(top_probs[0], top_indices[0])):
                food_name = self.model.config.id2label[idx.item()]
                confidence = prob.item()
                
                # Keep top prediction even if confidence is low, otherwise enforce threshold
                if rank == 0 or confidence >= self.min_confidence:
                    gluten_risk = self._get_gluten_risk_for_food(food_name)
                    detected_foods.append({
                        "name": food_name,
                        "confidence": round(confidence, 3),
                        "gluten_risk": gluten_risk
                    })
            
            if detected_foods:
                return detected_foods
            
            # Fall back to the best model prediction instead of "unknown"
            best_idx = top_indices[0][0].item()
            best_prob = top_probs[0][0].item()
            best_name = self.model.config.id2label[best_idx]
            return [{
                "name": best_name,
                "confidence": round(best_prob, 3),
                "gluten_risk": self._get_gluten_risk_for_food(best_name)
            }]
            
        except Exception as e:
            import traceback
            print(f"❌ Detection error: {e}")
            print(traceback.format_exc())
            return [{"name": "unknown", "confidence": 0.0, "gluten_risk": 0}]
    
    def _get_gluten_risk_for_food(self, food_name: str) -> int:
        """
        Map food name to gluten risk score (0-100)
        """
        food_lower = food_name.lower()
        
        # Check for direct matches
        for keyword, risk in self.gluten_keywords.items():
            if keyword in food_lower:
                return risk
        
        # Check for partial matches - Western foods
        if any(word in food_lower for word in ["bread", "wheat", "flour", "dough"]):
            return 95
        if any(word in food_lower for word in ["pasta", "noodle", "spaghetti"]):
            return 95
        if any(word in food_lower for word in ["cake", "cookie", "pastry", "pie"]):
            return 90
        if any(word in food_lower for word in ["fried", "breaded", "battered"]):
            return 70
        
        # Check for partial matches - Desi/South Asian foods
        if any(word in food_lower for word in ["roti", "chapati", "naan", "paratha", "puri", "bhatura", "kulcha"]):
            return 100  # All desi flatbreads contain wheat flour
        if any(word in food_lower for word in ["samosa", "kachori", "mathri"]):
            return 90  # Pastry-based snacks
        if any(word in food_lower for word in ["pakora", "bhaji", "bonda"]):
            return 85  # Batter-fried items
        if any(word in food_lower for word in ["dal", "daal", "lentil", "curry", "sabzi"]):
            return 5  # Usually gluten-free
        if any(word in food_lower for word in ["raita", "dahi", "lassi"]):
            return 5  # Yogurt-based, gluten-free
        if any(word in food_lower for word in ["pulao", "pulav", "biryani"]):
            return 5  # Rice-based, but check if served with naan/roti
        
        # Safe foods
        if any(word in food_lower for word in ["rice", "quinoa", "potato", "aloo"]):
            return 5
        if any(word in food_lower for word in ["salad", "vegetable", "fruit", "kachumber"]):
            return 10
        
        # Default: moderate risk for unknown foods
        return 30
    
    def _calculate_gluten_risk(self, detected_foods: List[Dict[str, Any]]) -> float:
        """
        Calculate overall gluten risk score for the meal
        Weighted by confidence
        """
        if not detected_foods:
            return 0.0
        
        total_weighted_risk = 0.0
        total_weight = 0.0
        
        for food in detected_foods:
            confidence = food["confidence"]
            gluten_risk = food["gluten_risk"]
            
            total_weighted_risk += confidence * gluten_risk
            total_weight += confidence
        
        if total_weight == 0:
            return 0.0
        
        return round(total_weighted_risk / total_weight, 1)
    
    # ============================================================================
    # ADAPTIVE DIP RECOMMENDATION SYSTEM - Quality Analysis & Recommendations
    # ============================================================================
    # New intelligent layer that analyzes image quality and recommends optimal
    # DIP techniques before processing. Completely non-intrusive - can be enabled
    # or disabled without affecting existing functionality.
    # ============================================================================
    
    def _analyze_image_quality(self, image: np.ndarray) -> Dict[str, float]:
        """
        Phase 1: Analyze image quality metrics
        
        Calculates:
        - Brightness (mean intensity, 0-255)
        - Contrast (std deviation of intensities)
        - Noise level (variance in local neighborhoods)
        - Sharpness (Laplacian variance - gradient magnitude)
        - Edge density (percentage of edge pixels)
        - Color saturation (HSV S-channel mean)
        
        Returns dict with normalized scores (0-100) for each metric.
        Reference: Image quality assessment fundamentals (Week 2-3 DIP syllabus)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        
        # 1. Brightness Assessment (Mean pixel intensity)
        brightness_raw = np.mean(gray)
        brightness_score = min(100, max(0, (brightness_raw / 255.0) * 100))
        
        # 2. Contrast Assessment (Standard deviation)
        contrast_raw = np.std(gray)
        contrast_score = min(100, max(0, (contrast_raw / 128.0) * 100))
        
        # 3. Noise Level Assessment (Variance in local neighborhoods)
        # Apply Sobel filter to detect edges, then calculate variance
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
        
        # Calculate noise as variance in flat regions (low gradient areas)
        flat_regions = gradient_magnitude < np.percentile(gradient_magnitude, 50)
        if np.any(flat_regions):
            noise_variance = np.var(gray[flat_regions])
            noise_score = min(100, max(0, (noise_variance / 500.0) * 100))
        else:
            noise_score = 50.0  # Default moderate noise
        
        # 4. Sharpness Assessment (Laplacian variance - gradient magnitude)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness_raw = np.var(laplacian)
        sharpness_score = min(100, max(0, (sharpness_raw / 500.0) * 100))
        
        # 5. Edge Density Assessment (Percentage of edge pixels)
        edges = cv2.Canny(gray, 50, 150)
        edge_pixels = np.sum(edges > 0)
        edge_density_raw = (edge_pixels / (h * w)) * 100
        edge_density_score = min(100, max(0, edge_density_raw * 2))  # Scale up
        
        # 6. Color Saturation Assessment (HSV S-channel mean)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        saturation = hsv[:, :, 1]  # S channel
        saturation_raw = np.mean(saturation)
        color_saturation_score = min(100, max(0, (saturation_raw / 255.0) * 100))
        
        return {
            "brightness": round(brightness_raw, 2),
            "brightness_score": round(brightness_score, 2),
            "contrast": round(contrast_raw, 2),
            "contrast_score": round(contrast_score, 2),
            "noise": round(noise_variance if np.any(flat_regions) else 250.0, 2),
            "noise_score": round(noise_score, 2),
            "sharpness": round(sharpness_raw, 2),
            "sharpness_score": round(sharpness_score, 2),
            "edge_density": round(edge_density_raw, 2),
            "edge_density_score": round(edge_density_score, 2),
            "color_saturation": round(saturation_raw, 2),
            "color_saturation_score": round(color_saturation_score, 2)
        }
    
    def _recommend_dip_techniques(self, quality_metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Phase 2: Rule-based recommendation engine
        
        Analyzes quality metrics and recommends optimal DIP techniques.
        No training required - pure rule-based logic.
        
        Returns:
        - recommended_technique: Name of best technique (e.g., "CLAHE", "Bilateral Filter")
        - recommendation_reason: Explanation string
        - alternatives: List of alternative techniques to compare
        - problems_detected: List of quality issues found
        """
        brightness = quality_metrics["brightness_score"]
        contrast = quality_metrics["contrast_score"]
        noise = quality_metrics["noise_score"]
        sharpness = quality_metrics["sharpness_score"]
        color_sat = quality_metrics["color_saturation_score"]
        edge_density = quality_metrics["edge_density_score"]
        
        problems_detected = []
        recommendations = []
        
        # Problem 1: Dark image
        if brightness < 60:
            problems_detected.append("Dark image (brightness: {:.1f}/100)".format(brightness))
            recommendations.append({
                "technique": "CLAHE",
                "priority": 1,
                "reason": "Image is too dark. CLAHE (Contrast Limited Adaptive Histogram Equalization) will improve visibility while preserving local contrast."
            })
        
        # Problem 2: Low contrast
        if contrast < 40:
            problems_detected.append("Low contrast ({:.1f}/100)".format(contrast))
            if "CLAHE" not in [r["technique"] for r in recommendations]:
                recommendations.append({
                    "technique": "CLAHE",
                    "priority": 1,
                    "reason": "Low contrast detected. CLAHE will enhance contrast adaptively without over-saturating."
                })
            else:
                recommendations.append({
                    "technique": "Histogram Equalization",
                    "priority": 2,
                    "reason": "Alternative: Global histogram equalization can improve contrast across the entire image."
                })
        
        # Problem 3: High noise
        if noise > 60:
            problems_detected.append("High noise level ({:.1f}/100)".format(noise))
            recommendations.append({
                "technique": "Bilateral Filter",
                "priority": 1,
                "reason": "High noise detected. Bilateral filter will reduce noise while preserving edges important for food detection."
            })
            recommendations.append({
                "technique": "Non-local Means Denoising",
                "priority": 2,
                "reason": "Alternative: Advanced denoising technique effective for food images."
            })
        
        # Problem 4: Blurry image
        if sharpness < 40 and edge_density < 10:
            problems_detected.append("Blurry image (sharpness: {:.1f}/100, edge density: {:.1f}/100)".format(sharpness, edge_density))
            recommendations.append({
                "technique": "Laplacian Sharpening",
                "priority": 1,
                "reason": "Image appears blurry with low edge density. Sharpening will enhance edges for better food feature detection."
            })
        
        # Problem 5: Dull colors
        if color_sat < 40:
            problems_detected.append("Low color saturation ({:.1f}/100)".format(color_sat))
            recommendations.append({
                "technique": "HSV Saturation Enhancement",
                "priority": 2,
                "reason": "Dull colors detected. Saturation enhancement can improve food region visibility."
            })
        
        # Default: Good quality image
        if not recommendations:
            problems_detected.append("Good image quality - minimal preprocessing needed")
            recommendations.append({
                "technique": "Gaussian Smoothing",
                "priority": 1,
                "reason": "Image quality is good. Minimal smoothing recommended to preserve natural details."
            })
        
        # Sort by priority
        recommendations.sort(key=lambda x: x["priority"])
        
        # Get recommended technique (highest priority)
        recommended = recommendations[0]
        
        # Get alternatives (next 2 recommendations)
        alternatives = [r for r in recommendations[1:4]]
        if len(alternatives) < 2:
            # Add common alternatives if not enough
            default_alts = [
                {"technique": "Histogram Equalization", "reason": "Standard contrast enhancement"},
                {"technique": "Gaussian Blur", "reason": "Standard smoothing filter"}
            ]
            for alt in default_alts:
                if alt["technique"] not in [r["technique"] for r in recommendations]:
                    alternatives.append(alt)
                    if len(alternatives) >= 2:
                        break
        
        return {
            "recommended_technique": recommended["technique"],
            "recommendation_reason": recommended["reason"],
            "problems_detected": problems_detected,
            "alternatives": alternatives[:2],  # Limit to 2 alternatives
            "all_recommendations": recommendations
        }
    
    def _apply_enhancement_technique(self, image: np.ndarray, technique_name: str) -> np.ndarray:
        """
        Apply a specific enhancement technique to the image.
        Helper function for technique comparison.
        """
        if technique_name == "CLAHE":
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l_enhanced = clahe.apply(l)
            enhanced_lab = cv2.merge([l_enhanced, a, b])
            return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        elif technique_name == "Histogram Equalization":
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            hist_eq = cv2.equalizeHist(gray)
            return cv2.cvtColor(hist_eq, cv2.COLOR_GRAY2BGR)
        
        elif technique_name == "Bilateral Filter":
            return cv2.bilateralFilter(image, 9, 75, 75)
        
        elif technique_name == "Non-local Means Denoising":
            return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        
        elif technique_name == "Laplacian Sharpening":
            kernel = np.array([[-1, -1, -1],
                              [-1,  9, -1],
                              [-1, -1, -1]])
            return cv2.filter2D(image, -1, kernel)
        
        elif technique_name == "HSV Saturation Enhancement":
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            hsv[:, :, 1] = cv2.multiply(hsv[:, :, 1], 1.5)  # Increase saturation by 50%
            hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
            return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        elif technique_name == "Gaussian Smoothing" or technique_name == "Gaussian Blur":
            return cv2.GaussianBlur(image, (5, 5), 0)
        
        else:
            # Default: return original
            return image.copy()
    
    def _calculate_psnr(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        Calculate Peak Signal-to-Noise Ratio (PSNR) between two images.
        Reference: Wang, Z., et al. "Image quality assessment: from error visibility to structural similarity." IEEE TIP, 2004.
        """
        # Ensure same size
        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        
        # Convert to grayscale if color
        if len(img1.shape) == 3:
            img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        # Calculate MSE
        mse = np.mean((img1.astype(np.float64) - img2.astype(np.float64)) ** 2)
        
        if mse == 0:
            return 100.0  # Perfect match
        
        max_pixel = 255.0
        psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
        
        return round(psnr, 2)
    
    def _calculate_ssim(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        Calculate Structural Similarity Index (SSIM) between two images.
        Reference: Wang, Z., et al. "A universal image quality index." IEEE Signal Processing Letters, 2002.
        
        Uses skimage.metrics.structural_similarity if available, otherwise uses fallback calculation.
        """
        # Ensure same size
        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        
        # Convert to grayscale if color
        if len(img1.shape) == 3:
            img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        else:
            img1_gray = img1
            img2_gray = img2
        
        if SSIM_AVAILABLE:
            try:
                # Use skimage's SSIM function
                ssim = ssim_func(img1_gray, img2_gray, data_range=255)
                return round(float(ssim), 3)
            except Exception as e:
                print(f"⚠️ SSIM calculation failed, using fallback: {e}")
        
        # Fallback: Simplified SSIM calculation
        # This is a basic approximation - not as accurate as full SSIM but works
        mu1 = np.mean(img1_gray)
        mu2 = np.mean(img2_gray)
        
        sigma1_sq = np.var(img1_gray)
        sigma2_sq = np.var(img2_gray)
        
        sigma12 = np.mean((img1_gray - mu1) * (img2_gray - mu2))
        
        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2
        
        ssim = ((2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)) / ((mu1**2 + mu2**2 + C1) * (sigma1_sq + sigma2_sq + C2))
        
        return round(float(ssim), 3)
    
    def _calculate_image_entropy(self, image: np.ndarray) -> float:
        """
        Calculate image entropy (information content).
        Higher entropy = more information content.
        Formula: entropy = -sum(p * log2(p)) where p = normalized histogram
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Calculate histogram
        hist, _ = np.histogram(gray.flatten(), bins=256, range=(0, 256))
        
        # Normalize
        hist = hist.astype(np.float64)
        hist = hist / np.sum(hist)
        
        # Remove zeros to avoid log(0)
        hist = hist[hist > 0]
        
        # Calculate entropy
        entropy = -np.sum(hist * np.log2(hist))
        
        return round(float(entropy), 3)
    
    def _calculate_gradient_magnitude(self, image: np.ndarray) -> float:
        """
        Calculate gradient magnitude (sharpness metric).
        Higher value = sharper image.
        Formula: variance of Laplacian
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        gradient_magnitude = np.var(laplacian)
        
        return round(float(gradient_magnitude), 2)
    
    def _compare_technique_effectiveness(self, original: np.ndarray, 
                                        recommended: np.ndarray,
                                        alternatives: List[Tuple[str, np.ndarray]]) -> Dict[str, Any]:
        """
        Phase 3: Compare effectiveness of different enhancement techniques.
        
        Calculates quality metrics (PSNR, SSIM, Entropy, Gradient Magnitude) for:
        - Original image (baseline)
        - Recommended technique
        - Alternative techniques
        
        Returns comprehensive comparison metrics.
        """
        results = {
            "original": {
                "psnr": None,  # PSNR not applicable for original
                "ssim": 1.0,   # Perfect match to itself
                "entropy": self._calculate_image_entropy(original),
                "gradient_magnitude": self._calculate_gradient_magnitude(original)
            },
            "recommended": {
                "technique": "Recommended",
                "psnr": self._calculate_psnr(original, recommended),
                "ssim": self._calculate_ssim(original, recommended),
                "entropy": self._calculate_image_entropy(recommended),
                "gradient_magnitude": self._calculate_gradient_magnitude(recommended)
            },
            "alternatives": []
        }
        
        # Calculate metrics for alternatives
        for alt_name, alt_image in alternatives:
            alt_metrics = {
                "technique": alt_name,
                "psnr": self._calculate_psnr(original, alt_image),
                "ssim": self._calculate_ssim(original, alt_image),
                "entropy": self._calculate_image_entropy(alt_image),
                "gradient_magnitude": self._calculate_gradient_magnitude(alt_image)
            }
            results["alternatives"].append(alt_metrics)
        
        # Calculate improvements for recommended technique
        recommended_psnr = results["recommended"]["psnr"]
        recommended_ssim = results["recommended"]["ssim"]
        recommended_entropy = results["recommended"]["entropy"]
        original_entropy = results["original"]["entropy"]
        
        results["improvements"] = {
            "psnr_improvement": f"+{recommended_psnr:.1f}dB" if recommended_psnr else "N/A",
            "ssim_improvement": f"+{(recommended_ssim - 1.0) * 100:.1f}%" if recommended_ssim != 1.0 else "0%",
            "entropy_improvement": f"{((recommended_entropy - original_entropy) / original_entropy * 100):.1f}%" if original_entropy > 0 else "0%"
        }
        
        return results
    
    def _generate_quality_assessment_dashboard(self, quality_metrics: Dict[str, float],
                                               recommendation: Dict[str, Any],
                                               output_dir: str, base_filename: str) -> str:
        """
        Phase 4: Generate quality assessment dashboard (radar chart).
        
        Creates a professional radar/spider chart showing all quality metrics
        with color-coded scores and recommendation overlay.
        """
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        # Prepare data for radar chart
        categories = ['Brightness', 'Contrast', 'Sharpness', 'Edge Density', 'Color Saturation', 'Noise (inverse)']
        scores = [
            quality_metrics["brightness_score"],
            quality_metrics["contrast_score"],
            quality_metrics["sharpness_score"],
            quality_metrics["edge_density_score"],
            quality_metrics["color_saturation_score"],
            100 - quality_metrics["noise_score"]  # Invert noise (lower is better)
        ]
        
        # Number of variables
        N = len(categories)
        
        # Compute angle for each axis
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Complete the circle
        
        # Complete the scores list
        scores += scores[:1]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        # Plot
        ax.plot(angles, scores, 'o-', linewidth=2, color='#4ECDC4', label='Image Quality')
        ax.fill(angles, scores, alpha=0.25, color='#4ECDC4')
        
        # Add color-coded zones
        for i, score in enumerate(scores[:-1]):
            color = 'green' if score >= 70 else ('yellow' if score >= 40 else 'red')
            ax.plot([angles[i], angles[i+1]], [0, 100], color=color, alpha=0.1, linewidth=20)
        
        # Customize
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=11, fontweight='bold')
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=9)
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # Add title and recommendation
        recommended_tech = recommendation.get("recommended_technique", "N/A")
        title = f'Image Quality Assessment Dashboard\nRecommended Technique: {recommended_tech}'
        plt.title(title, size=14, fontweight='bold', pad=20)
        
        # Add legend
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        
        # Save
        dashboard_path = os.path.join(output_dir, f"{base_filename}_quality_assessment_dashboard.png")
        plt.savefig(dashboard_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return dashboard_path
    
    def _generate_enhancement_comparison(self, original: np.ndarray,
                                        recommended: np.ndarray, recommended_name: str,
                                        alternatives: List[Tuple[str, np.ndarray]],
                                        comparison_metrics: Dict[str, Any],
                                        output_dir: str, base_filename: str) -> str:
        """
        Generate enhancement comparison grid (4 images side-by-side).
        
        Shows: Original | Recommended | Alternative 1 | Alternative 2
        With PSNR and SSIM metrics below each image.
        """
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        # Prepare images and labels
        images = [
            (original, "Original", comparison_metrics["original"]),
            (recommended, recommended_name, comparison_metrics["recommended"])
        ]
        
        # Add alternatives
        for alt_name, alt_img in alternatives[:2]:
            # Find metrics for this alternative
            alt_metrics = next(
                (a for a in comparison_metrics["alternatives"] if a["technique"] == alt_name),
                None
            )
            if alt_metrics:
                images.append((alt_img, alt_name, alt_metrics))
        
        # Create figure with 4 subplots
        fig, axes = plt.subplots(1, 4, figsize=(16, 4))
        
        for idx, (img, label, metrics) in enumerate(images[:4]):  # Limit to 4
            # Convert BGR to RGB for display
            if len(img.shape) == 3:
                display_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            else:
                display_img = img
            
            axes[idx].imshow(display_img)
            axes[idx].axis('off')
            
            # Format metrics text
            psnr_text = f"PSNR: {metrics.get('psnr', 'N/A')}dB" if metrics.get('psnr') else "PSNR: N/A"
            ssim_text = f"SSIM: {metrics.get('ssim', 1.0):.3f}"
            entropy_text = f"Entropy: {metrics.get('entropy', 0):.2f}"
            
            # Add title and metrics
            title = label
            if idx == 1:  # Recommended
                title += " ⭐"
            
            axes[idx].set_title(title, fontsize=11, fontweight='bold', pad=5)
            
            # Add metrics below image
            metrics_text = f"{psnr_text}\n{ssim_text}\n{entropy_text}"
            axes[idx].text(0.5, -0.15, metrics_text, ha='center', va='top',
                          transform=axes[idx].transAxes, fontsize=9,
                          bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Hide unused subplots
        for idx in range(len(images), 4):
            axes[idx].axis('off')
        
        plt.suptitle('Enhancement Technique Comparison', fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        
        comparison_path = os.path.join(output_dir, f"{base_filename}_enhancement_comparison.png")
        plt.savefig(comparison_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return comparison_path
    
    def _generate_quality_metrics_bar_chart(self, comparison_metrics: Dict[str, Any],
                                            output_dir: str, base_filename: str) -> str:
        """
        Generate quality metrics bar chart comparing all techniques.
        
        Shows: PSNR, SSIM, Entropy, Gradient Magnitude
        Bars: Original | Recommended | Alternative 1 | Alternative 2
        """
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        # Prepare data
        techniques = ["Original"]
        psnr_values = [None]  # Original doesn't have PSNR
        ssim_values = [comparison_metrics["original"]["ssim"]]
        entropy_values = [comparison_metrics["original"]["entropy"]]
        gradient_values = [comparison_metrics["original"]["gradient_magnitude"]]
        
        # Add recommended
        rec = comparison_metrics["recommended"]
        techniques.append("Recommended")
        psnr_values.append(rec.get("psnr"))
        ssim_values.append(rec.get("ssim"))
        entropy_values.append(rec.get("entropy"))
        gradient_values.append(rec.get("gradient_magnitude"))
        
        # Add alternatives
        for alt in comparison_metrics["alternatives"][:2]:
            techniques.append(alt["technique"][:15])  # Truncate long names
            psnr_values.append(alt.get("psnr"))
            ssim_values.append(alt.get("ssim"))
            entropy_values.append(alt.get("entropy"))
            gradient_values.append(alt.get("gradient_magnitude"))
        
        # Create figure with 4 subplots (one for each metric)
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        x = np.arange(len(techniques))
        width = 0.6
        
        # Color scheme
        colors = ['#95E1D3', '#4ECDC4', '#44A08D', '#F38181']
        
        # Plot 1: PSNR
        psnr_filtered = [v if v is not None else 0 for v in psnr_values]
        bars1 = axes[0, 0].bar(x, psnr_filtered, width, color=colors, alpha=0.8, edgecolor='black')
        axes[0, 0].set_ylabel('PSNR (dB)', fontweight='bold')
        axes[0, 0].set_title('Peak Signal-to-Noise Ratio', fontweight='bold', pad=10)
        axes[0, 0].set_xticks(x)
        axes[0, 0].set_xticklabels(techniques, rotation=15, ha='right')
        axes[0, 0].grid(True, alpha=0.3, axis='y')
        
        # Highlight recommended
        if len(techniques) > 1:
            bars1[1].set_color('#2ECC71')
            bars1[1].set_edgecolor('darkgreen')
            bars1[1].set_linewidth(2)
        
        # Add value labels
        for i, (bar, val) in enumerate(zip(bars1, psnr_values)):
            if val is not None:
                axes[0, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                               f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # Plot 2: SSIM
        bars2 = axes[0, 1].bar(x, ssim_values, width, color=colors, alpha=0.8, edgecolor='black')
        axes[0, 1].set_ylabel('SSIM Score', fontweight='bold')
        axes[0, 1].set_title('Structural Similarity Index', fontweight='bold', pad=10)
        axes[0, 1].set_xticks(x)
        axes[0, 1].set_xticklabels(techniques, rotation=15, ha='right')
        axes[0, 1].set_ylim(0, 1.1)
        axes[0, 1].grid(True, alpha=0.3, axis='y')
        
        # Highlight recommended
        if len(techniques) > 1:
            bars2[1].set_color('#2ECC71')
            bars2[1].set_edgecolor('darkgreen')
            bars2[1].set_linewidth(2)
        
        # Add value labels
        for bar, val in zip(bars2, ssim_values):
            axes[0, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                           f'{val:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # Plot 3: Entropy
        bars3 = axes[1, 0].bar(x, entropy_values, width, color=colors, alpha=0.8, edgecolor='black')
        axes[1, 0].set_ylabel('Entropy (bits)', fontweight='bold')
        axes[1, 0].set_title('Image Entropy (Information Content)', fontweight='bold', pad=10)
        axes[1, 0].set_xticks(x)
        axes[1, 0].set_xticklabels(techniques, rotation=15, ha='right')
        axes[1, 0].grid(True, alpha=0.3, axis='y')
        
        # Highlight recommended
        if len(techniques) > 1:
            bars3[1].set_color('#2ECC71')
            bars3[1].set_edgecolor('darkgreen')
            bars3[1].set_linewidth(2)
        
        # Add value labels
        for bar, val in zip(bars3, entropy_values):
            axes[1, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                           f'{val:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # Plot 4: Gradient Magnitude
        bars4 = axes[1, 1].bar(x, gradient_values, width, color=colors, alpha=0.8, edgecolor='black')
        axes[1, 1].set_ylabel('Gradient Magnitude', fontweight='bold')
        axes[1, 1].set_title('Sharpness (Laplacian Variance)', fontweight='bold', pad=10)
        axes[1, 1].set_xticks(x)
        axes[1, 1].set_xticklabels(techniques, rotation=15, ha='right')
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        # Highlight recommended
        if len(techniques) > 1:
            bars4[1].set_color('#2ECC71')
            bars4[1].set_edgecolor('darkgreen')
            bars4[1].set_linewidth(2)
        
        # Add value labels
        for bar, val in zip(bars4, gradient_values):
            axes[1, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + val*0.02,
                           f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
        
        plt.suptitle('Quality Metrics Comparison Across Techniques', fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        
        bar_chart_path = os.path.join(output_dir, f"{base_filename}_quality_metrics_comparison.png")
        plt.savefig(bar_chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return bar_chart_path
    
    def _generate_quality_metrics_table(self, comparison_metrics: Dict[str, Any],
                                       recommendation: Dict[str, Any],
                                       output_dir: str, base_filename: str) -> str:
        """
        Generate quality metrics comparison table (PNG image).
        
        Creates a professional table showing all metrics for all techniques.
        """
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        # Prepare data
        table_data = []
        headers = ['Technique', 'PSNR (dB)', 'SSIM', 'Entropy', 'Gradient']
        
        # Add original
        orig = comparison_metrics["original"]
        table_data.append([
            'Original',
            'N/A',
            f'{orig["ssim"]:.3f}',
            f'{orig["entropy"]:.2f}',
            f'{orig["gradient_magnitude"]:.1f}'
        ])
        
        # Add recommended
        rec = comparison_metrics["recommended"]
        table_data.append([
            f"{recommendation['recommended_technique']} ⭐",
            f'{rec.get("psnr", "N/A")}' if rec.get("psnr") else 'N/A',
            f'{rec.get("ssim", 0):.3f}',
            f'{rec.get("entropy", 0):.2f}',
            f'{rec.get("gradient_magnitude", 0):.1f}'
        ])
        
        # Add alternatives
        for alt in comparison_metrics["alternatives"][:2]:
            table_data.append([
                alt["technique"],
                f'{alt.get("psnr", "N/A")}' if alt.get("psnr") else 'N/A',
                f'{alt.get("ssim", 0):.3f}',
                f'{alt.get("entropy", 0):.2f}',
                f'{alt.get("gradient_magnitude", 0):.1f}'
            ])
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.axis('tight')
        ax.axis('off')
        
        # Create table
        table = ax.table(cellText=table_data, colLabels=headers, cellLoc='center',
                        loc='center', bbox=[0, 0, 1, 1])
        
        # Style table
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        # Color header row
        for i in range(len(headers)):
            cell = table[(0, i)]
            cell.set_facecolor('#4ECDC4')
            cell.set_text_props(weight='bold', color='white')
        
        # Highlight recommended row
        if len(table_data) > 1:
            for i in range(len(headers)):
                cell = table[(1, i)]
                cell.set_facecolor('#E8F8F5')
                cell.set_text_props(weight='bold')
        
        # Style data rows
        for row in range(1, len(table_data)):
            for col in range(len(headers)):
                cell = table[(row, col)]
                if row % 2 == 0:
                    cell.set_facecolor('#F9F9F9')
        
        plt.title('Quality Metrics Comparison Table', fontsize=14, fontweight='bold', pad=20)
        
        table_path = os.path.join(output_dir, f"{base_filename}_quality_metrics_table.png")
        plt.savefig(table_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return table_path
    
    
    def _run_adaptive_dip_analysis(self, image: np.ndarray, output_dir: str, base_filename: str) -> Dict[str, Any]:
        """
        Main integration function: Run complete adaptive DIP analysis pipeline.
        
        This function orchestrates:
        1. Image quality analysis
        2. Technique recommendation
        3. Technique application and comparison
        4. Visualization generation
        
        Returns comprehensive results dictionary with all metrics and file paths.
        """
        results = {
            "quality_analysis": {},
            "recommendations": {},
            "comparison_metrics": {},
            "visualizations": {},
            "status": "success"
        }
        
        try:
            # Phase 1: Analyze image quality
            print("🔬 Adaptive DIP: Analyzing image quality...")
            quality_metrics = self._analyze_image_quality(image)
            results["quality_analysis"] = quality_metrics
            
            # Phase 2: Get recommendations
            print("🔬 Adaptive DIP: Generating technique recommendations...")
            recommendation = self._recommend_dip_techniques(quality_metrics)
            results["recommendations"] = recommendation
            
            # Phase 3: Apply recommended technique and alternatives
            print("🔬 Adaptive DIP: Applying and comparing techniques...")
            recommended_technique = recommendation["recommended_technique"]
            recommended_image = self._apply_enhancement_technique(image, recommended_technique)
            
            # Save recommended technique result
            recommended_path = os.path.join(output_dir, f"{base_filename}_recommended_{recommended_technique.lower().replace(' ', '_')}.jpg")
            cv2.imwrite(recommended_path, recommended_image)
            results["visualizations"]["recommended_image"] = recommended_path
            
            # Apply alternatives
            alternatives = []
            for alt_rec in recommendation.get("alternatives", [])[:2]:
                alt_name = alt_rec.get("technique", "")
                alt_image = self._apply_enhancement_technique(image, alt_name)
                alternatives.append((alt_name, alt_image))
            
            # Phase 4: Compare techniques
            comparison_metrics = self._compare_technique_effectiveness(
                image, recommended_image, alternatives
            )
            results["comparison_metrics"] = comparison_metrics
            
            # Phase 5: Generate visualizations
            print("🔬 Adaptive DIP: Generating visualizations...")
            
            # Quality assessment dashboard
            dashboard_path = self._generate_quality_assessment_dashboard(
                quality_metrics, recommendation, output_dir, base_filename
            )
            results["visualizations"]["quality_dashboard"] = dashboard_path
            
            # Enhancement comparison grid
            comparison_grid_path = self._generate_enhancement_comparison(
                image, recommended_image, recommended_technique,
                alternatives, comparison_metrics, output_dir, base_filename
            )
            results["visualizations"]["enhancement_comparison"] = comparison_grid_path
            
            # Quality metrics bar chart
            bar_chart_path = self._generate_quality_metrics_bar_chart(
                comparison_metrics, output_dir, base_filename
            )
            results["visualizations"]["quality_metrics_bar_chart"] = bar_chart_path
            
            # Quality metrics table
            table_path = self._generate_quality_metrics_table(
                comparison_metrics, recommendation, output_dir, base_filename
            )
            results["visualizations"]["quality_metrics_table"] = table_path
            
            # Recommendation explanation (with comparison metrics)
            explanation_path = self._fix_recommendation_explanation_comparison_metrics(
                comparison_metrics, quality_metrics, recommendation, output_dir, base_filename
            )
            results["visualizations"]["recommendation_explanation"] = explanation_path
            
            print(f"✅ Adaptive DIP Analysis Complete - {len(results['visualizations'])} visualizations generated")
            
        except Exception as e:
            import traceback
            print(f"⚠️ Adaptive DIP analysis failed (non-critical): {e}")
            print(traceback.format_exc())
            results["status"] = "failed"
            results["error"] = str(e)
        
        return results
    
    def _fix_recommendation_explanation_comparison_metrics(self, comparison_metrics: Dict[str, Any],
                                                           quality_metrics: Dict[str, float],
                                                           recommendation: Dict[str, Any],
                                                           output_dir: str, base_filename: str) -> str:
        """
        Fixed version of recommendation explanation that properly receives comparison_metrics.
        """
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
        
        fig, ax = plt.subplots(figsize=(14, 8))
        ax.axis('off')
        
        # Define positions
        y_positions = [0.8, 0.5, 0.2]
        
        # Box 1: Image Analysis
        problems_text = '\n'.join(recommendation.get("problems_detected", ["None"]))
        if len(problems_text) > 100:
            problems_text = problems_text[:100] + "..."
        
        box1 = FancyBboxPatch((0.1, y_positions[0] - 0.15), 0.25, 0.3,
                              boxstyle="round,pad=0.01", facecolor='#E8F8F5', edgecolor='#4ECDC4', linewidth=2)
        ax.add_patch(box1)
        ax.text(0.225, y_positions[0], 'Image Quality\nAnalysis', ha='center', va='center',
               fontsize=11, fontweight='bold', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        ax.text(0.225, y_positions[0] - 0.08, problems_text, ha='center', va='top',
               fontsize=9, style='italic')
        
        # Arrow 1
        arrow1 = FancyArrowPatch((0.35, y_positions[0]), (0.45, y_positions[1]),
                                arrowstyle='->', mutation_scale=20, lw=2, color='#4ECDC4')
        ax.add_patch(arrow1)
        
        # Box 2: Problems & Solution
        recommended_tech = recommendation.get("recommended_technique", "N/A")
        reason = recommendation.get("recommendation_reason", "N/A")
        if len(reason) > 80:
            reason = reason[:80] + "..."
        
        box2 = FancyBboxPatch((0.5, y_positions[1] - 0.15), 0.25, 0.3,
                              boxstyle="round,pad=0.01", facecolor='#FFF4E6', edgecolor='#FFA726', linewidth=2)
        ax.add_patch(box2)
        ax.text(0.625, y_positions[1] + 0.05, f'Recommended:\n{recommended_tech}', ha='center', va='center',
               fontsize=11, fontweight='bold')
        ax.text(0.625, y_positions[1] - 0.08, reason, ha='center', va='top',
               fontsize=9, style='italic')
        
        # Arrow 2
        arrow2 = FancyArrowPatch((0.75, y_positions[1]), (0.85, y_positions[2]),
                                arrowstyle='->', mutation_scale=20, lw=2, color='#FFA726')
        ax.add_patch(arrow2)
        
        # Box 3: Expected Improvement
        improvements = comparison_metrics.get("improvements", {})
        psnr_imp = improvements.get("psnr_improvement", "N/A")
        ssim_imp = improvements.get("ssim_improvement", "N/A")
        improvement_text = f"Improvements:\n• PSNR: {psnr_imp}\n• SSIM: {ssim_imp}\n• Better detection"
        
        box3 = FancyBboxPatch((0.9, y_positions[2] - 0.15), 0.25, 0.3,
                              boxstyle="round,pad=0.01", facecolor='#E3F2FD', edgecolor='#2196F3', linewidth=2)
        ax.add_patch(box3)
        ax.text(1.025, y_positions[2], 'Expected\nImprovement', ha='center', va='center',
               fontsize=11, fontweight='bold')
        ax.text(1.025, y_positions[2] - 0.08, improvement_text, ha='center', va='top',
               fontsize=9)
        
        plt.title('DIP Technique Recommendation Flow', fontsize=16, fontweight='bold', pad=20)
        
        explanation_path = os.path.join(output_dir, f"{base_filename}_recommendation_explanation.png")
        plt.savefig(explanation_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return explanation_path
