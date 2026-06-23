# TAA AI Perishable Demand Forecasting Presentation Script

This script accompanies the slide deck for presenting the AI-Powered Perishable Demand Forecasting System to Thai AirAsia (TAA) management. It contains both English and Thai versions for each slide.

---

## Slide 1: Title Slide
**Slide Title:** AI-Powered Perishable Demand Forecasting  
**Visuals:** Warm dark background, AirAsia Red and Gold sunrise gradient accent stripe, prominent typography.

### Speaking Script (English):
> "Good morning, team. Today, I am excited to present our new AI-Powered Perishable Demand Forecasting and Inventory Optimization System for our DMK–MLE–DMK sector. This project transitions Thai AirAsia from manual stocking heuristics to an advanced, automated operations research pipeline. It allows us to maximize in-flight retail revenue while dramatically reducing food wastage."

### บทพูด (ภาษาไทย):
> "สวัสดีครับ/ค่ะทีมงานทุกท่าน วันนี้ผม/ดิฉันมีความยินดีที่จะนำเสนอระบบพยากรณ์ความต้องการและเพิ่มประสิทธิภาพสินค้าประเภทของสดเน่าเสียง่ายด้วยพลัง AI (AI-Powered Perishable Demand Forecasting and Inventory Optimization System) สำหรับเส้นทางบิน DMK-MLE-DMK โครงการนี้จะเปลี่ยนผ่านจากการจัดการสต็อกด้วยการคาดเดาแบบเดิม (Manual Heuristics) ไปสู่ระบบปัญญาประดิษฐ์ขั้นสูงเพื่อช่วยเพิ่มรายได้สูงสุดและลดปริมาณขยะอาหารได้อย่างมีนัยสำคัญครับ"

---

## Slide 2: The Spoilage & Stockout Crisis
**Slide Title:** The Operational Crisis  
**Visuals:** Highlighted early 2026 performance figures: 23–34% sell-through rate vs. 12–20% stockout rate.

### Speaking Script (English):
> "To understand why this system is critical, let's look at the numbers from early 2026. Under our legacy manual stocking methods, we faced a double penalty. We were discarding between 65% to 76% of all loaded perishable food at the end of the round trip, yet we still suffered from a 12% to 20% stockout rate on our best-selling items. We were literally throwing away three out of every four meals while leaving high-margin customer demand unsatisfied."

### บทพูด (ภาษาไทย):
> "เพื่อที่จะทำความเข้าใจว่าทำไมระบบนี้ถึงมีความสำคัญ เรามาดูตัวเลขในช่วงต้นปี 2026 กันครับ ภายใต้วิธีการทำงานแบบเดิม เราต้องเจอกับผลกระทบทั้งสองด้านคือ มีอัตราอาหารสูญเสีย (Wastage) สูงถึง 65% - 76% หรือพูดง่ายๆ ว่าเราต้องทิ้งอาหารสดถึง 3 ใน 4 กล่องเมื่อสิ้นสุดเที่ยวบินขากลับ ในทางตรงกันข้าม เรากลับเจอปัญหาสินค้าขายดีหมดเกลี้ยง (Stockout) สูงถึง 12% - 20% ทำให้เราเสียโอกาสในการขายสินค้าที่มีมาร์จินสูงและต้องแบกรับต้นทุนอาหารที่เสียเปล่าไปด้วย"

---

## Slide 3: The Pair-Route Decision Unit
**Slide Title:** The Atomic Unit: Pair-Route Aggregation  
**Visuals:** Schematic of DMK → MLE → DMK round-trip collapse.

### Speaking Script (English):
> "Our first breakthrough is redefining the decision unit. Because replenishment occurs exclusively at DMK to minimize outstation turnaround times, any leg-by-leg planning is mathematically incorrect. Additionally, cabin crew often log transactions from the return leg under the outbound sector, corrupting leg-by-leg sales data. By collapsing Sector 1 and Sector 2 into a single pair-route unit, we completely eliminate crew logging errors and simplify stockout tracking."

### บทพูด (ภาษาไทย):
> "ทางออกแรกของเราคือการปรับเปลี่ยนหน่วยการตัดสินใจใหม่ (Decision Unit) เนื่องจากเที่ยวบินนี้มีการเติมอาหารสดเฉพาะที่ดอนเมือง (DMK) เท่านั้น เพื่อลดระยะเวลาการจอดของเครื่องบินที่มาเล (MLE) การวางแผนแยกทีละขาจึงไม่ถูกต้องตามหลักคณิตศาสตร์และขั้นตอนการปฏิบัติงาน นอกจากนี้ ลูกเรือมักจะคีย์ยอดขายขากลับปะปนไปกับขาไป ทำให้ข้อมูลรายขาเกิดความคลาดเคลื่อน ดังนั้น การรวมเที่ยวบินไป-กลับเข้าด้วยกันเป็น 'หน่วยเส้นทางบินแบบคู่' (Pair-Route Unit) จึงช่วยแก้ปัญหานี้และทำให้เราติดตามปัญหาสินค้าหมดได้แม่นยำ 100% ครับ"

---

## Slide 4: Recovering True Demand (Tobit MLE)
**Slide Title:** Demand Censoring & Tobit MLE  
**Visuals:** Equation or chart showing how sales drop to zero when stockouts occur, hiding true latent demand.

### Speaking Script (English):
> "Standard forecasting models fail because when an item runs out, sales drop to zero, hiding the true latent demand. This is called 'demand censoring'. To solve this, our engine runs a Tobit Maximum Likelihood Estimation. This statistical model reconstructs the historical demand curve, allowing the system to learn the true average demand and standard deviation even during stockouts."

### บทพูด (ภาษาไทย):
> "โมเดลพยากรณ์ทั่วไปมักจะให้ผลพยากรณ์ที่ต่ำกว่าความเป็นจริง เพราะเมื่อสินค้าหมด ยอดขายจะกลายเป็นศูนย์ ทำให้ไม่เห็นความต้องการที่แท้จริงของลูกค้า หรือที่เรียกว่า 'Demand Censoring' เพื่อแก้ไขปัญหานี้ ระบบของเราจึงนำแบบจำลอง Tobit MLE เข้ามาประยุกต์ใช้เพื่อคำนวณและกู้คืนเส้นโค้งความต้องการที่แท้จริงในอดีต ทำให้ระบบเรียนรู้ค่าเฉลี่ยความต้องการ (μ) และส่วนเบี่ยงเบนมาตรฐาน (σ) ในแต่ละเดือนได้อย่างถูกต้องแม้จะมีปัญหาสินค้าหมดสต็อกก็ตาม"

---

## Slide 5: The Math: Step-by-Step Q* Calculation Pipeline
**Slide Title:** Step-by-Step Q* Calculation Pipeline  
**Visuals:** Structural workflow detailing Step 1 (Tobit Rate Estimation), Step 2 (Margin Service Level), Step 3 (Baseline Scaling), and Step 4 (Demographic Mix Scaling).

### Speaking Script (English):
> "Now let's step under the hood to see exactly how the AI model calculates the optimal load quantity, which we call Q*. The pipeline works in four sequential steps. 
> First, it fits the Tobit MLE model on our 3-year history of per-passenger demand rates to isolate the true mean and standard deviation rate per calendar month.
> Second, it solves the Critical Fractile using price and cost margins to find our target z-score safety buffer. 
> Third, it scales these rates by the upcoming flight's Net Boarded Passenger count to produce a baseline. 
> Fourth, it adjusts this baseline by our demographic mix Gamma factor to determine the final, optimized Q* quantity to load at DMK."

### บทพูด (ภาษาไทย):
> "เราลองมาเจาะลึกขั้นตอนการคำนวณของ AI ในการหาปริมาณการโหลดที่เหมาะสมที่สุด หรือที่เราเรียกว่าค่า Q* กันครับ ระบบจะทำงานตาม 4 ขั้นตอนหลัก ดังนี้:
> ขั้นตอนที่ 1 ประเมินความต้องการรายบุคคล (Tobit Rate Estimation - T2): ฟิตโมเดล Tobit บนอัตราส่วนยอดขายต่อผู้โดยสารที่แท้จริง ย้อนหลัง 3 ปี เพื่อหาค่าเฉลี่ยความต้องการ (μ_rate) และการกระจายตัว (σ_rate) ในแต่ละเดือน
> ขั้นตอนที่ 2 หาอัตราส่วนการให้บริการที่เหมาะสมตามกำไร (Critical Fractile - T3/T4): คำนวณอัตราส่วนวิกฤต (Critical Ratio) จากราคาขายและต้นทุน เพื่อหาค่า z-score สำหรับการโหลดเผื่อที่ปลอดภัย
> ขั้นตอนที่ 3 คำนวณยอดพยากรณ์ตั้งต้น (Baseline Scaling - T5): นำอัตราความต้องการมาคูณกับจำนวนผู้โดยสารสุทธิ (Net BoB) ของเที่ยวบินนั้นๆ
> ขั้นตอนที่ 4 ปรับระดับตามความหลากหลายของสัญชาติ (Demographic Scaling - T5b): ใช้ตัวคูณ Gamma (γ) ปรับค่าพยากรณ์ให้ตรงกับสัญชาติของผู้โดยสารบนไฟลท์จริง เพื่อได้ยอดแนะนำโหลด Q* สุดท้ายที่จะบรรทุกขึ้นจากดอนเมืองครับ"

---

## Slide 6: The 7-Theory Operations Research Pipeline
**Slide Title:** The 7-Theory Operations Research Pipeline  
**Visuals:** Bulleted list detailing Theories T1 through T7 split across two visual panels.

### Speaking Script (English):
> "To establish absolute mathematical rigor, our system implements 7 core operations research theories. These span from Theory 1, which aggregates the pair-route data, to Theory 2's Tobit demand censoring, Theory 3 and 4's Newsvendor optimization and Critical Fractile margins, Theory 5 and 5b's capacity and demographic scaling, and finally Theory 6 and 7's product substitution for cold starts and post-flight actuals refitting feedback loop. This pipeline ensures every loading decision is backed by validated quantitative theories."

### บทพูด (ภาษาไทย):
> "เพื่อสร้างความแม่นยำทางคณิตศาสตร์อย่างสมบูรณ์ ระบบของเราใช้ทฤษฎีวิจัยดำเนินงาน (Operations Research) หลัก 7 ทฤษฎีด้วยกันครับ เริ่มตั้งแต่ทฤษฎีที่ 1 (T1) การรวมยอดขายรายคู่เที่ยวบิน, ทฤษฎีที่ 2 (T2) แบบจำลอง Tobit กู้คืนความต้องการแท้จริง, ทฤษฎีที่ 3 (T3) และ 4 (T4) การเพิ่มประสิทธิภาพกำไรด้วย Newsvendor และ Critical Fractile, ทฤษฎีที่ 5 (T5) และ 5b (T5b) การปรับเพิ่มลดตามจำนวนผู้โดยสารและสัญชาติจริง และปิดท้ายด้วยทฤษฎีที่ 6 (T6) และ 7 (T7) การกำหนดเมนูตัวแทนช่วงเริ่มซีซั่นใหม่และการฟิตโมเดลย้อนหลังด้วยยอดขายจริงหลังเครื่องลง ซึ่งทฤษฎีทั้งหมดนี้จะทำงานสอดประสานกันเพื่อรับประกันความแม่นยำในทุกการตัดสินใจครับ"

---

## Slide 7: The Critical Fractile & Newsvendor Model
**Slide Title:** The Critical Fractile  
**Visuals:** Table of margins and critical ratios (F*) for top items like Boba Tea (59%) and Basil Chicken (68%).

### Speaking Script (English):
> "Since our perishable items carry healthy margins, the financial penalty for under-catering (lost sales) is significantly higher than the cost of over-catering (wasted food cost). Using the Newsvendor model, the system calculates a 'Critical Ratio' for each SKU. The optimization engine uses this ratio to recommend a positive safety stock buffer, skewing our loading quantities above the mean demand to maximize overall flight profitability."

### บทพูด (ภาษาไทย):
> "เนื่องจากสินค้าประเภทอาหารสดของเรามีส่วนต่างกำไรที่ดีมาก ค่าปรับทางการเงินจากการโหลดสินค้าขาด (โอกาสสูญเสียรายได้) จึงสูงกว่าต้นทุนการโหลดสินค้าเกิน (ต้นทุนอาหารที่ต้องทิ้ง) ระบบ Newsvendor จึงใช้ Critical Ratio ของแต่ละเมนู เช่น ชานมไข่มุก (59%) หรือ ข้าวกะเพราไก่ (68%) เพื่อกำหนดจุดบริการที่ดีที่สุด โมเดลจะแนะนำให้โหลดสต็อกสำรอง (Safety Stock Buffer) เหนือกว่าค่าเฉลี่ยทั่วไป เพื่อคว้าโอกาสสร้างรายได้สูงสุดในช่วงเวลาที่มีการเดินทางหนาแน่นครับ"

---

## Slide 8: Passenger Demographic Insights
**Slide Title:** Demographic Buying Behavior  
**Visuals:** Demographics breakdown: Thai (comfort food, Boba), Chinese (savory, BoB surgers), Maldivian (spicy cup noodles).

### Speaking Script (English):
> "Our data joins revealed high-value behavioral patterns. For example, Thai passengers are proactive pre-bookers (making up to 69% of pre-booked meals), whereas Chinese tourists rarely pre-book. However, because Chinese passengers make up half the flight load during summer peaks, they drive massive surges in in-flight Buy-on-Board sales. We must stock enough hot meals to capture this high-volume in-flight demand."

### บทพูด (ภาษาไทย):
> "จากการวิเคราะห์ข้อมูลเชิงลึกของผู้โดยสาร เราพบพฤติกรรมที่น่าสนใจมากครับ เช่น ผู้โดยสารชาวไทยจะเป็นกลุ่มที่ซื้ออาหารล่วงหน้าค่อนข้างสูง (สั่ง pre-booked สูงถึง 69% ของยอดทั้งหมด) ในขณะที่ผู้โดยสารชาวจีนแทบจะไม่ pre-book เลย (เพียง 8% - 20% เท่านั้น) อย่างไรก็ตาม ในช่วงไฮซีซั่นฤดูร้อน เที่ยวบินจะมีชาวจีนเดินทางเป็นสัดส่วนครึ่งหนึ่งของลำ ซึ่งผู้โดยสารชาวจีนกลุ่มนี้จะไปซื้ออาหารบนเครื่องแบบ Buy-on-Board ทดแทน ดังนั้น เราต้องเตรียมอาหารให้เพียงพอเพื่อรองรับความต้องการที่พุ่งขึ้นกระทันหันบนเครื่องครับ"

---

## Slide 9: Pre-Flight Demographic Scaling
**Slide Title:** Pre-Flight Scaling (Theory T5b)  
**Visuals:** Formula block showing the Gamma (γ) multiplier adjusting baseline Q* based on upcoming manifest composition.

### Speaking Script (English):
> "Two to three days before departure, the operations team uploads the passenger manifest. The system calculates a demographic 'Gamma' multiplier. If the upcoming flight has a higher proportion of Chinese passengers than the historical monthly average, the system automatically inflates the recommendation for Teriyaki and reduces spicier Thai-preferred items. This gives us flight-specific precision."

### บทพูด (ภาษาไทย):
> "ในช่วง 2-3 วันก่อนวันบิน ทีมปฏิบัติการจะทำการอัปโหลดรายชื่อผู้โดยสารเข้าระบบ ระบบจะนำมาคำนวณหาค่าตัวคูณสัญชาติหรือ 'Gamma' ตัวอย่างเช่น หากเที่ยวบินนั้นมีสัดส่วนผู้โดยสารชาวจีนมากกว่าเกณฑ์เฉลี่ยปกติ ระบบจะปรับเพิ่มยอดสั่งโหลดเมนูเทอริยากิ และปรับลดยอดสั่งโหลดเมนูกะเพราไก่ที่มีรสชาติเผ็ดลงอัตโนมัติ ซึ่งช่วยเพิ่มความแม่นยำรายเที่ยวบินได้อย่างดีเยี่ยมครับ"

---

## Slide 10: Data Cleanliness: The Water Code Correction
**Slide Title:** Water Code Exclusions  
**Visuals:** Impact highlight: 37.6% of PBM rows are water codes, causing a systematic 8–11% Q* underestimation when unfiltered.

### Speaking Script (English):
> "Data cleanliness is key. Previously, bottled water pre-orders were counted under the perishable meal denominator in our live uploads, but correctly excluded from historical training. This mismatch resulted in an 8% to 11% systematic underestimation of our food forecast. We fixed this by automatically filtering out water codes, ensuring our denominators match perfectly."

### บทพูด (ภาษาไทย):
> "ความสะอาดของข้อมูลเป็นสิ่งสำคัญมากครับ ในอดีตระบบบันทึกยอดพรีออเดอร์ของน้ำดื่มขวดรวมเข้าไปใน denominator ของอาหารสดด้วย ซึ่งทำให้ N_active หรือจำนวนผู้โดยสารที่มีโอกาสซื้ออาหารบนเครื่องในระบบพยากรณ์คลาดเคลื่อน ส่งผลให้เกิดการคำนวณโหลดต่ำกว่าความเป็นจริงถึง 8% - 11% เราจึงได้ทำการตัดโค้ดที่เป็นน้ำดื่ม (BWFD, BWAK, BWHL, WBHL) ออกจากการวิเคราะห์อาหารสดทั้งหมด เพื่อลบความคลาดเคลื่อนและทำให้สถิติการเรียนรู้ตรงกันครับ"

---

## Slide 11: Projected Financial Impact
**Slide Title:** Financial Performance Turnaround  
**Visuals:** Profit comparisons: BOBA MILK TEA turnaround from -13k THB to +74k THB; Chicken Rice profit up 53%.

### Speaking Script (English):
> "The bottom-line impact is substantial. When we run this optimized model on our historical database, we see a massive turnaround. For instance, Boba Thai Milk Tea—which suffered a net loss due to severe manual over-provisioning in low-demand months—turns around to a positive profit of over 74,000 THB. Other core hot meals see profit uplifts between 17% and 53% by aligning inventory with demand."

### บทพูด (ภาษาไทย):
> "เมื่อเรานำโมเดลไปทดสอบย้อนหลัง ผลลัพธ์ทางการเงินแสดงให้เห็นถึงจุดเปลี่ยนที่ชัดเจน ตัวอย่างเช่น ชานมไข่มุก (BOBA MILK TEA) ซึ่งเดิมมีผลประกอบการขาดทุนสะสมกว่า -13,000 บาท เนื่องจากความผิดพลาดในการโหลดเผื่อมากเกินไปในโลว์ซีซั่น ได้พลิกกลับมาสร้างกำไรกว่า 74,600 บาท และเมนูหลักอื่นๆ เช่น ข้าวมันไก่อาชิน ก็มีกำไรเพิ่มขึ้นถึง 53.6% จากการปรับสต็อกให้สมดุลตามฤดูกาลครับ"

---

## Slide 12: Operational Workflow
**Slide Title:** The Operational Cycle  
**Visuals:** Two-step flowchart: Pre-flight (Manifest Upload & Forecast) and Post-flight (Actuals Upload & MLE Refit).

### Speaking Script (English):
> "The system is designed for daily airline operations. Pre-flight, the dispatcher uploads the manifest, receives the Q* recommendation, and loads the catering at DMK. Post-flight, the crew uploads actual sales and boarded passengers. This post-flight data is fed back into the engine, executing a Theory 7 MLE Refit to update the historical parameters for all future flights."

### บทพูด (ภาษาไทย):
> "ระบบนี้ออกแบบมาให้ใช้งานง่ายในชีวิตประจำวัน: ก่อนบิน (Pre-Flight) ดิสแพตเชอร์เพียงอัปโหลดไฟล์รายชื่อผู้โดยสารและข้อมูล pre-booked เพื่อให้ระบบแนะนำยอดโหลด Q* และจัดสรรขึ้นเครื่องขากลางวัน ส่วนหลังบิน (Post-Flight) ก็จะทำการอัปโหลดข้อมูลยอดขายจริง ขยะอาหาร และจำนวนผู้โดยสารที่เดินทางจริงเพื่อนำเข้าสู่การปรับปรุงแบบจำลองใหม่ (Theory 7 MLE Refit) สำหรับเที่ยวบินถัดไปครับ"

---

## Slide 13: Summary & Next Steps
**Slide Title:** Empowering TAA Retail  
**Visuals:** Bullet points: Minimize food waste, Maximize in-flight revenue, Scale to other sectors.

### Speaking Script (English):
> "In summary, this system bridges advanced operations research with day-to-day cabin retail. We minimize spoilage, capture lost sales, and establish a repeatable model for TAA. Our next steps are to scale this solution to other high-capacity sectors and explore dynamic markdown strategies on the return leg. Thank you, and I welcome any questions."

### บทพูด (ภาษาไทย):
> "โดยสรุป ระบบนี้คือการนำงานวิจัยเชิงปฏิบัติการเข้ามาผสานเข้ากับงานขายหน้าร้านบนเที่ยวบินของแอร์เอเชียอย่างสมบูรณ์แบบ ช่วยลดความสูญเสีย เพิ่มรายได้ และสร้างกระบวนการที่เป็นมาตรฐาน สำหรับก้าวต่อไป เราเตรียมขยายระบบพยากรณ์นี้ไปยังเส้นทางบินข้ามประเทศหลักอื่นๆ และพัฒนาการปรับลดราคาสินค้าขากลับเพื่อระบายสต็อกคงเหลือครับ ขอขอบคุณทุกท่าน และยินดีรับฟังคำถามครับ"
