<script setup lang="ts">
import { ref, computed } from 'vue'
import { NPageHeader, NSpace, NText, NBreadcrumb, NInputGroupLabel, NIcon, NSwitch, NLayoutContent, NAvatar, NCheckbox, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, NInput, NInputGroup } from 'naive-ui'
import { HomeIcon, RootIcon, BatchIcon, GoIcon, ProviderIcon, ReleaseIcon } from '../../components/icons'
import { useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import BatchBreadcrumbItem from '../../components/breadcrumbs/BatchBreadcrumbItem.vue'
import ProducerOptionsSetter from '../../components/metadata/ProducerOptionsSetter.vue'
import { useStore } from '../../services/store'
import { ProducerOptions, Provider } from '../../models'
import ProviderSetter from '../../components/metadata/ProviderSetter.vue'

const store = useStore();
const router = useRouter();

const inputProvider = ref<Provider>(new Provider());
const inputValue = ref<string>("coxbuild");
const inputOptions = ref<ProducerOptions>(new ProducerOptions());

function onGo() {
    router.push({
        path: `/batching/${inputProvider.value}/${inputValue.value}/`,
        query: <any>inputOptions.value,
    });
}

</script>

<template>
    <n-page-header title="Batching" subtitle="Aexpy" @back="() => router.back()">
        <template #avatar>
            <n-avatar>
                <n-icon>
                    <BatchIcon />
                </n-icon>
            </n-avatar>
        </template>
        <template #header>
            <n-breadcrumb>
                <HomeBreadcrumbItem />
                <BatchBreadcrumbItem />
            </n-breadcrumb>
        </template>
        <template #footer>
            <n-space vertical>
                <n-input-group size="large">
                    <ProviderSetter :provider="inputProvider" />
                    <n-input-group-label size="large">
                        <n-icon>
                            <ReleaseIcon />
                        </n-icon>
                    </n-input-group-label>
                    <n-input v-model:value="inputValue" placeholder="Release" size="large"></n-input>
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