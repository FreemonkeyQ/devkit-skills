package com.kuavo.datahub.common.tool;

import com.baomidou.mybatisplus.core.MybatisConfiguration;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.TableInfoHelper;
import com.kuavo.core.secure.utils.SecureUtil;
import com.kuavo.datahub.modules.system.entity.Dept;
import org.apache.ibatis.builder.MapperBuilderAssistant;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.mockito.MockedStatic;

import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mockStatic;

class LetHiddenDeptIsolationTest {

	@BeforeAll
	static void initTableInfo() {
		TableInfoHelper.initTableInfo(
			new MapperBuilderAssistant(new MybatisConfiguration(), ""), Dept.class);
	}

	@Test
	void 组织隔离的Lambda版本包含子项目条件() {
		try (MockedStatic<SecureUtil> secure = mockStatic(SecureUtil.class)) {
			secure.when(SecureUtil::getIsolationType).thenReturn("department");
			secure.when(SecureUtil::getUserDeptId).thenReturn("dept-1");
			LambdaQueryWrapper<Dept> wrapper = new LambdaQueryWrapper<>();
			DataIsolationUtil.setDeptIsolation(wrapper);
			String sql = wrapper.getSqlSegment();
			assertTrue(sql.contains("type"), sql);
			assertTrue(sql.contains("parent_id"), sql);
			assertTrue(wrapper.getParamNameValuePairs().containsValue("dept-1"),
				wrapper.getParamNameValuePairs().toString());
		}
	}

}
