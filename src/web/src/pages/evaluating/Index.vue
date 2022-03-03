<script setup lang="ts">
import { ref, computed } from 'vue'
import { NPageHeader, NSpace, NText, NSwitch, NBreadcrumb, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, NInput, NInputGroup } from 'naive-ui'
import { HomeIcon, RootIcon, EvaluateIcon, GoIcon, ProviderIcon, ReleaseIcon } from '../../components/icons'
import { useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import EvaluateBreadcrumbItem from '../../components/breadcrumbs/EvaluateBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { ProducerOptions, Provider, Release, ReleasePair } from '../../models'
import ProducerOptionsSetter from '../../components/metadata/ProducerOptionsSetter.vue'
import ReleasePairSetter from '../../components/metadata/ReleasePairSetter.vue'
import ProviderSetter from '../../components/metadata/ProviderSetter.vue'

const store = useStore();
const router = useRouter();

const inputProvider = ref<Provider>(new Provider());
const inputValue = ref<ReleasePair>(new ReleasePair(new Release("click", "0.3"), new Release("click", "0.4")));
const inputOptions = ref<ProducerOptions>(new ProducerOptions());

function onGo() {
    router.push({
        path: `/evaluating/${inputProvider.value}/${inputValue.value.toString()}/`,
        query: <any>inputOptions.value,
    });
}

</script>

<template>
    <n-page-header title="Evaluating" subtitle="Aexpy" @back="() => router.back()">
        <template #avatar>
            <n-avatar>
                <n-icon>
                    <EvaluateIcon />
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
                    <ProviderSetter :provider="inputProvider" />
                    <ReleasePairSetter :pair="inputValue" />
                    <n-button type="primary" @click="onGo" :style="{ width: '10%'}" size="large">
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