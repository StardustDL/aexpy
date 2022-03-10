<script setup lang="ts">
import { ref, computed } from 'vue'
import { NPageHeader, NSpace, NText, NBreadcrumb, NInputGroupLabel, NIcon, NSwitch, NLayoutContent, NPopconfirm, NAvatar, NCheckbox, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, NInput, NInputGroup } from 'naive-ui'
import { HomeIcon, RootIcon, BatchIcon, GoIcon, ProviderIcon, BatchIndexIcon, ReleaseIcon } from '../../components/icons'
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

function onGoIndex() {
    router.push({
        path: `/batching/${inputProvider.value}/${inputValue.value}/`,
        query: <any>{
            index: true,
            ...inputOptions.value
        },
    });
}

</script>

<template>
    <n-space vertical>
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
                        <n-input
                            v-model:value="inputValue"
                            placeholder="Release"
                            size="large"
                            @keyup.enter="onGoIndex"
                        ></n-input>
                        <n-popconfirm @positive-click="onGo">
                            <template #trigger>
                                <n-button
                                    type="primary"
                                    ghost
                                    :style="{ width: '5%' }"
                                    size="large"
                                >
                                    <n-icon size="large">
                                        <GoIcon />
                                    </n-icon>
                                </n-button>
                            </template>
                            This command will cost much time, are you sure?
                        </n-popconfirm>
                        <n-button
                            type="primary"
                            @click="onGoIndex"
                            :style="{ width: '5%' }"
                            size="large"
                        >
                            <n-icon size="large">
                                <BatchIndexIcon />
                            </n-icon>
                        </n-button>
                    </n-input-group>
                    <ProducerOptionsSetter :options="inputOptions" />
                </n-space>
            </template>
        </n-page-header>

        <iframe
            :src="`${store.state.api.baseUrl}/data/batching`"
            :style="{ 'border-width': '0px', 'width': '100%', 'height': '600px' }"
        ></iframe>
    </n-space>
</template>