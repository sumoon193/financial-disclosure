package com.example.financialdisclosure.agent;

import io.agentscope.core.model.Model;
import io.agentscope.extensions.model.dashscope.DashScopeChatModel;
import io.agentscope.harness.agent.HarnessAgent;
import java.nio.file.Path;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AgentScopeConfiguration {
    @Bean
    @ConditionalOnProperty(name = "financial.agent.enabled", havingValue = "true")
    HarnessAgent financialExplanationAgent(
            @Value("${QWEN_API_KEY:}") String apiKey,
            @Value("${QWEN_CHAT_MODEL:qwen-plus}") String modelName,
            @Value("${financial.agent.workspace:./runtime/agentscope}") Path workspace) {
        if (apiKey.isBlank()) {
            throw new IllegalStateException(
                    "QWEN_API_KEY is required when financial.agent.enabled=true");
        }
        Model model =
                DashScopeChatModel.builder()
                        .apiKey(apiKey)
                        .modelName(modelName)
                        .stream(false)
                        .build();
        return HarnessAgent.builder()
                .name("financial-disclosure-explainer")
                .sysPrompt(
                        "只解释服务端已用 BigDecimal 计算并附带引用的财务事实。"
                                + "不得自行计算金额，不得忽略引用，不确定时要求人工复核。")
                .model(model)
                .workspace(workspace)
                .build();
    }
}
