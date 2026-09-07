# 4T4R_DV_Test_筛选不正常的数据
## 第1步
- only read filename include AllData
- Time == NaN,跳过

## 第2步
- 对于列名rbAdc_DebugData_st.rbAdc_VbatVoltage_u16 > 16*1000,就不正常
- 对于列名含有Temp(大小写都需要),要求只要有一个大于135,就不正常
- 对于列名含有Pmic,要求只要有一个不为0,就不正常
- g_rbRsp_ErrorTableArm.m_value._0_.errorCounter != 0,就不正常
- 第2步的四个要求,只要满足一个就不正常,抛出！

## 第3步
- 对于列名 rba_DemBfm_Records._0_.eventId 到 rba_DemBfm_Records._19_.eventId,此20列
- 此20列中有下包含的数字为number_error_id,白名单为white_number_error=[0,11,9,22,12,72,65,139,168,159,170,86,169,140,141,78,16,174,153,77,108,116,156]
- 白名单id就不用管,否则,就不正常,进入第四步

## 第4步
对于第3步如果不正常,找到对于Dem_AllEventsStatusByte._number_error_id_
- 有Dem_AllEventsStatusByte._1_到Dem_AllEventsStatusByte._177_,看它是否为单数,选择当前故障，双数为历史故障。抛出故障（故障英文，简化）！

## 第5步
- 输出为output文件夹(主动创建),文件名同源文件,输入为文件夹，文件夹里的csv
- ttk,其中white_number_error可配置,初始化为white_number_error
- white_number_error的配置gui人性化！

## 第6步
- 导出此文件csv
- 表头和行输出顺序为：
- time，故障（故障英文，包含具体错误数值），number_error_id(20列，rba_DemBfm_Records._0_.eventId 到 rba_DemBfm_Records._19_.eventId，白名单直接赋值-1，其余为原始值)，rbAdc_DebugData_st.rbAdc_VbatVoltage_u16，列名含有Temp的列，列名含有Pmic的列，g_rbRsp_ErrorTableArm.m_value._0_.errorCounter
