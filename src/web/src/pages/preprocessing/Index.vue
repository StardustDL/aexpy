<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NPageHeader, NSpace, NSelect, SelectOption, NText, NSwitch, NBreadcrumb, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, NInput, NInputGroup } from 'naive-ui'
import { HomeIcon, RootIcon, PreprocessIcon, GoIcon, ProviderIcon, ReleaseIcon } from '../../components/icons'
import { useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import PreprocessBreadcrumbItem from '../../components/breadcrumbs/PreprocessBreadcrumbItem.vue'
import { useStore } from '../../services/store'
import { ProducerOptions, Provider, Release } from '../../models'
import ProducerOptionsSetter from '../../components/metadata/ProducerOptionsSetter.vue'
import ReleaseSetter from '../../components/metadata/ReleaseSetter.vue'
import ProviderSetter from '../../components/metadata/ProviderSetter.vue'

const store = useStore();
const router = useRouter();

const inputProvider = ref<Provider>(new Provider());
const inputValue = ref<Release>(new Release("coxbuild", "0.1.0"));
const inputOptions = ref<ProducerOptions>(new ProducerOptions());

function onGo() {
    router.push({
        path: `/preprocessing/${inputProvider.value.toString()}/${inputValue.value.toString()}/`,
        query: <any>inputOptions.value,
    });
}
</script>

<template>
    <n-page-header title="Preprocessing" subtitle="Aexpy" @back="() => router.back()">
        <template #avatar>
            <n-avatar>
                <n-icon>
                    <PreprocessIcon />
                </n-icon>
            </n-avatar>
        </template>
        <template #header>
            <n-breadcrumb>
                <HomeBreadcrumbItem />
                <PreprocessBreadcrumbItem />
            </n-breadcrumb>
        </template>
        <template #footer>
            <n-space vertical>
                <n-input-group size="large">
                    <ProviderSetter :provider="inputProvider" />
                    <ReleaseSetter :release="inputValue" />
                    <n-button type="primary" @click="onGo" :style="{ width: '10%' }" size="large">
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