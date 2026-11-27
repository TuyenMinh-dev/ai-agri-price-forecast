KIỂM TOÁN NGUỒN DỮ LIỆU – AGRISIGHT

1. Mục đích

Tài liệu này mô tả nguồn dữ liệu đầu vào, cơ chế thu thập, lưu trữ và kiểm tra nguồn gốc dữ liệu của hệ thống dự báo giá nông sản AgriSight.

Mục tiêu là bảo đảm dữ liệu sử dụng trong hệ thống có thể truy xuất nguồn gốc, phân biệt dữ liệu thực tế với dữ liệu thử nghiệm và hạn chế việc tạo dự báo khi dữ liệu đầu vào không đủ điều kiện.

2. Nguồn dữ liệu giá nông sản

2.1. Nguồn dữ liệu đang được sử dụng

Nguồn thu thập

Nguồn dữ liệu gốc

Nhóm dữ liệu

vietnambiz.vn

giacaphe.com

Cà phê, hồ tiêu

vietnambiz.vn

luagaoviet.com

Lúa gạo

Các crawler trong dự án sử dụng thông tin giá được thu thập từ Vietnambiz và ghi nhận nguồn dữ liệu gốc tương ứng.

Các file crawler liên quan:

scripts/crawler/coffee/crawl_coffee.py

scripts/crawler/pepper/crawl_pepper.py

scripts/crawler/rice/crawl_rice.py

scripts/crawler/rice/backfill_rice_history.py

2.2. Cơ chế thu thập và lưu trữ

Quy trình dữ liệu giá:

Crawler thu thập dữ liệu giá từ nguồn.

Dữ liệu được xử lý và chuẩn hóa.

Thông tin nguồn được ghi vào trường source.

Script scripts/db/load_crawler_data.py đọc dữ liệu và lưu vào cơ sở dữ liệu.

Bảng MarketPrice lưu giá theo sản phẩm, ngày và nguồn dữ liệu.

Bảng MarketPrice sử dụng các thông tin quan trọng:

product_id: Mã sản phẩm.

price_date: Ngày ghi nhận giá.

price_avg: Giá trung bình.

source: Nguồn dữ liệu.

Cơ chế này giúp truy xuất nguồn gốc và hỗ trợ kiểm tra khi phát hiện dữ liệu bất thường.

3. Kiểm toán trường nguồn dữ liệu (Data Provenance)

3.1. Kết quả kiểm tra thực tế

Cơ sở dữ liệu đã được kiểm tra bằng truy vấn thống kê trên bảng MarketPrice.

Chỉ tiêu

Kết quả

Tổng số bản ghi giá

1.767

Bản ghi thiếu source

0

Bản ghi có source

1.767

Tỷ lệ bản ghi có nguồn

100%

Các giá trị nguồn được ghi nhận:

Giá trị source

Số bản ghi

vietnambiz.vn (gốc: giacaphe.com)

456

vietnambiz.vn (goc: luagaoviet.com)

1.114

vietnambiz.vn (gốc: luagaoviet.com)

197

Có sự khác biệt về cách viết goc và gốc trong dữ liệu nguồn. Đây là vấn đề chuẩn hóa tên nguồn, không phải bản ghi thiếu nguồn.

3.2. Đánh giá

Trường source đã được triển khai trong mô hình MarketPrice.

Crawler có ghi nhận nguồn dữ liệu.

Script nạp dữ liệu sử dụng thông tin nguồn khi lưu vào cơ sở dữ liệu.

Toàn bộ 1.767 bản ghi được kiểm tra đều có thông tin nguồn.

Như vậy, hệ thống đã triển khai được khả năng truy xuất nguồn gốc dữ liệu giá.

4. Nguồn dữ liệu thời tiết – NASA POWER

4.1. Nguồn dữ liệu

Hệ thống sử dụng NASA POWER API để thu thập dữ liệu thời tiết theo ngày.

API:

https://power.larc.nasa.gov/api/temporal/daily/point

Vị trí được sử dụng:

Khu vực: Đồng bằng sông Cửu Long.

Tọa độ: Cần Thơ (10.0452, 105.7469).

Cần Thơ được chọn làm điểm đại diện tham khảo cho khu vực nghiên cứu. Dữ liệu tại một tọa độ không thể đại diện hoàn toàn cho mọi tỉnh và vùng trồng trong Đồng bằng sông Cửu Long.

4.2. Các biến thời tiết được thu thập

Script hiện tại sử dụng:

Biến

Ý nghĩa

T2M

Nhiệt độ không khí trung bình ở độ cao 2 mét

PRECTOTCORR

Lượng mưa hiệu chỉnh

T2M_MAX và T2M_MIN có thể được xem xét bổ sung trong tương lai, nhưng chưa được script hiện tại thu thập.

File thực hiện:

scripts/data_external/fetch_weather_data.py

4.3. Kết quả thu thập thực tế

Kết quả chạy script và kiểm tra cơ sở dữ liệu:

Chỉ tiêu

Kết quả

Số bản ghi thời tiết

84

Ngày bắt đầu

2026-09-01

Ngày kết thúc

2026-11-23

Bản ghi thiếu nhiệt độ hoặc lượng mưa

0

Nhiệt độ trung bình tại ngày cuối

27,18

Lượng mưa tại ngày cuối

3,84

Dữ liệu được lưu vào bảng WeatherData.

Thời điểm dữ liệu thời tiết mới nhất có thể chậm hơn ngày hiện tại do độ trễ cập nhật của nguồn.

5. Phân tích biến động danh mục sản phẩm

Trong quá trình chạy pipeline ngày 27/11/2026, hệ thống ghi nhận một số sản phẩm có lịch sử cập nhật khác nhau:

Sản phẩm

Ngày cập nhật cuối được ghi nhận

Trạng thái pipeline

NL CL 555

11/11/2026

Bỏ qua

Tấm 3,4

26/09/2026

Bỏ qua

NL OM 5451

21/11/2026

Bỏ qua theo điều kiện pipeline

NL IR 504

25/11/2026

Được dự báo

5.1. Lưu ý về tính thời vụ

Sự thay đổi danh mục sản phẩm có thể liên quan đến mùa vụ, nguồn cung, nhu cầu thị trường hoặc thay đổi danh mục niêm yết.

Tuy nhiên, việc một sản phẩm không xuất hiện trong các lần cập nhật tiếp theo chưa đủ để kết luận sản phẩm đã hết vụ thu hoạch hoặc ngừng sản xuất.

Tương tự, việc OM 5451 xuất hiện trong danh mục được ghi nhận chưa tự chứng minh nguyên nhân là do vụ Thu Đông.

Các nhận định về mùa vụ cần được đối chiếu thêm với thông tin từ nguồn dữ liệu gốc hoặc tài liệu nông nghiệp đáng tin cậy.

5.2. Cơ chế thích ứng của pipeline

Pipeline kiểm tra dữ liệu lịch sử trước khi tạo dự báo.

Các trường hợp có thể bị bỏ qua:

Sản phẩm không có đủ dữ liệu lịch sử để huấn luyện.

Sản phẩm có dữ liệu giá không hợp lệ.

Dữ liệu cập nhật quá cũ theo ngưỡng của pipeline.

Sản phẩm không đáp ứng điều kiện xử lý của mô hình.

Cơ chế này giúp hạn chế việc tạo dự báo từ dữ liệu không đủ điều kiện.

Việc bị bỏ qua không đồng nghĩa với việc sản phẩm đã ngừng sản xuất hoặc không còn giao dịch trên thị trường.

6. Tích hợp LSTM vào pipeline dự báo

File thực hiện:

ml/models/generate_forecast.py

Pipeline sử dụng kiến trúc PriceLSTM được định nghĩa trong train_baseline.py.

Các bước xử lý chính:

Lấy dữ liệu giá lịch sử của sản phẩm.

Kiểm tra giá trị thiếu, vô hạn và giá không hợp lệ.

Chuẩn hóa dữ liệu bằng MinMaxScaler.

Tạo các cửa sổ dữ liệu huấn luyện theo chuỗi thời gian.

Huấn luyện mô hình LSTM.

Dự báo các bước tiếp theo.

Chuyển kết quả về thang giá ban đầu.

Lưu hoặc cập nhật kết quả vào bảng forecasts.

6.1. Kết quả chạy kiểm chứng

Kết quả chạy pipeline ngày 27/11/2026:

9 sản phẩm đủ điều kiện có kết quả LSTM.

Tổng cộng 36 bản ghi dự báo được lưu hoặc cập nhật cho 4 mô hình.

Ngày dự báo: 28/11/2026.

API có thể truy vấn kết quả bằng bộ lọc model_name=LSTM.

Website hiển thị kết quả dự báo của LSTM cùng các mô hình khác.

Các kết quả này chứng minh LSTM đã được tích hợp vào quy trình sinh dự báo và kết quả có thể được truy xuất từ hệ thống.

7. Thử nghiệm sử dụng dữ liệu thời tiết

Dự án có thử nghiệm so sánh mô hình sử dụng đặc trưng giá với mô hình bổ sung đặc trưng thời tiết.

Các biến thời tiết thử nghiệm:

rainfall_mm: Lượng mưa.

temperature_avg: Nhiệt độ trung bình.

7.1. Kết quả thử nghiệm

Mô hình

MAPE không có thời tiết

MAPE có thời tiết

Linear Regression

0,83%

0,87%

Random Forest

1,46%

1,40%

XGBoost

1,72%

1,55%

Thử nghiệm sử dụng tập dữ liệu ghép theo ngày có thông tin thời tiết tương ứng. Có 695 dòng được giữ lại trong tập so sánh.

Kết quả cho thấy đặc trưng thời tiết cải thiện chỉ số MAPE của Random Forest và XGBoost trong thử nghiệm này, nhưng làm chỉ số của Linear Regression tăng nhẹ.

Đây mới là kết quả thử nghiệm trên phạm vi dữ liệu hiện có. Dữ liệu thời tiết còn ngắn và thử nghiệm chưa đánh giá LSTM, do đó chưa đủ cơ sở để kết luận thời tiết luôn cải thiện chất lượng dự báo.

Lưu ý: Đặc trưng thời tiết hiện chưa được tích hợp vào pipeline dự báo sản xuất generate_forecast.py.

8. Hướng cải tiến

Kiểm tra và chuẩn hóa thống nhất cách ghi tên nguồn trong trường source.

Tiếp tục thu thập dữ liệu giá theo thời gian để tăng độ dài chuỗi lịch sử.

Đối chiếu dữ liệu với nguồn gốc khi phát hiện giá bất thường.

Bổ sung tọa độ thời tiết ở nhiều khu vực trồng nếu cần phân tích theo tỉnh.

Đánh giá thêm tác động của thời tiết trên tập dữ liệu dài hơn.

Kiểm chứng các nhận định về mùa vụ bằng nguồn độc lập.

Theo dõi tình trạng cập nhật dữ liệu để hạn chế dự báo khi dữ liệu đã cũ.

Thiết lập và kiểm tra cơ chế tự động chạy pipeline theo lịch nếu hệ thống triển khai chưa có bộ lập lịch.

9. Kết luận

AgriSight đã triển khai quy trình thu thập, lưu trữ và truy xuất nguồn gốc dữ liệu giá nông sản thông qua trường source.

Dữ liệu thời tiết NASA POWER đã được thu thập và lưu trữ trong cơ sở dữ liệu. Mô hình LSTM đã được tích hợp vào pipeline dự báo, kết quả được lưu vào bảng forecasts và hiển thị trên website.

Các kết quả trong tài liệu được phân biệt giữa dữ liệu đã kiểm tra thực tế, kết quả thử nghiệm và những giả thuyết cần xác minh thêm. Điều này giúp bảo đảm tính minh bạch và khả năng kiểm toán của hệ thống.