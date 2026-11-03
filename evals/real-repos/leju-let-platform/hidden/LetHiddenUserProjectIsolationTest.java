package com.kuavo.datahub.common.tool;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.kuavo.core.secure.utils.SecureUtil;
import com.kuavo.datahub.modules.system.entity.User;
import org.junit.jupiter.api.Test;
import org.mockito.MockedStatic;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mockStatic;

class LetHiddenUserProjectIsolationTest {

	@Test
	void 项目隔离必须精确匹配项目ID() {
		try (MockedStatic<SecureUtil> secure = mockStatic(SecureUtil.class)) {
			secure.when(SecureUtil::getIsolationType).thenReturn("project");
			secure.when(SecureUtil::getUserDeptId).thenReturn("dept-1");
			secure.when(SecureUtil::getUserProjectId).thenReturn("proj-1,proj-2");
			QueryWrapper<User> wrapper = new QueryWrapper<>();
			DataIsolationUtil.setUserIsolation(wrapper);
			String sql = wrapper.getSqlSegment();
			assertFalse(sql.toUpperCase().contains("LIKE"), sql);
			Map<String, Object> params = wrapper.getParamNameValuePairs();
			assertTrue(params.containsValue("proj-1"), params.toString());
			assertTrue(params.containsValue("proj-2"), params.toString());
			assertFalse(params.values().stream()
				.map(String::valueOf)
				.anyMatch(value -> value.contains("%")), params.toString());
		}
	}

}
