<script setup lang="ts">
import { ref, computed } from 'vue'
import { NPageHeader, NSpace, NText, NSwitch, NBreadcrumb, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, NInput, NInputGroup } from 'naive-ui'
import { HomeIcon, RootIcon, ReportIcon, GoIcon, ProviderIcon, ReleaseIcon } from '../../components/icons'
import { useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import EvaluateBreadcrumbItem from '../../components/breadcrumbs/EvaluateBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { ProducerOptions } from '../../models'
import ProducerOptionsSetter from '../../components/metadata/ProducerOptionsSetter.vue'

const store = useStore();
const router = useRouter();

const inputProvider = ref<string>("default");
const inputValue = ref<string>("coxbuild@0.0.9:0.1.0");
const inputOptions = ref<ProducerOptions>(new ProducerOptions());

function onGo() {
    router.push({
        path: `/evaluating/${inputProvider.value}/${inputValue.value}/`,
        query: <any>inputOptions.value,
    });
}

</script>

<template>
    <n-page-header title="Evaluating" subtitle="Aexpy" @back="() => router.back()">
        <template #avatar>
            <n-avatar>
                <n-icon>
                    <ReportIcon />
                </n-icon>
            </n-avatar>
        </template>
        <template #header>
            <n-breadcrumb>
                <HomeBreadcrumbItem />
                <EvaluateBreadcrumbItem />
            </n-breadcrumb>
        </template>
        <template #footer>
            <n-space vertical>
                <n-input-group>
                    <n-input v-model:value="inputProvider" placeholder="Provider">
                        <template #prefix>
                            <n-icon size="large">
                                <ProviderIcon />
                            </n-icon>
                        </template>
                    </n-input>
                    <n-input v-model:value="inputValue" placeholder="Release">
                        <template #prefix>
                            <n-icon size="large">
                                <ReleaseIcon />
                            </n-icon>
                        </template>
                    </n-input>
                    <n-button type="primary" ghost @click="onGo">
                        <n-icon size="large">
                            <GoIcon />
                        </n-icon>
                    </n-button>
                </n-input-group>
                <ProducerOptionsSetter :options="inputOptions" />
            </n-space>
        </template>
    </n-page-header>
</template>