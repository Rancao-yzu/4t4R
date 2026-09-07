# 4T4R_DV_Test_温度监控
## 第1步
- only read filename include AllData
- Time == NaN,跳过

## 第2步
- 对于列名含有Temp(大小写都需要)，

## 第3步
- 根据第2步的筛选结果，对于列名含有Temp(大小写都需要)，按每一列计算平均值和最大值（对于列名含有Temp每一列）

## 第4步
- 输出第3步计算结果，注意在列名中区分是平均值或最大值，例如
rbAdc_uCTemperature_st.rbAdc_R5fTempValue_mean、rbAdc_uCTemperature_st.rbAdc_R5fTempValue_max

## 第5步
- 输出为output文件夹(主动创建),文件名同源文件,输入为文件夹，文件夹里的csv
- 导出此文件csv
- 表头和行输出顺序为：time,（对于列名含有Temp每一列的平均值和最大值）