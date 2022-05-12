<script setup lang="ts">
import { ref, computed } from 'vue'
import { NPageHeader, NSpace, NText, NSwitch, NBreadcrumb, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, NInput, NInputGroup } from 'naive-ui'
import { HomeIcon, RootIcon, DiffIcon, GoIcon, ProviderIcon, ReleaseIcon } from '../../components/icons'
import { useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import DiffBreadcrumbItem from '../../components/breadcrumbs/DiffBreadcrumbItem.vue'
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
        path: `/differing/${inputProvider.value}/${inputValue.value.toString()}/`,
        query: <any>inputOptions.value,
    });
}

</script>

<template>
    <n-space vertical>
        <n-page-header title="Differing" subtitle="AexPy" @back="() => router.back()">
            <template #avatar>
                <n-avatar>
                    <n-icon>
                        <DiffIcon />
                    </n-icon>
                </n-avatar>
            </template>
            <template #header>
                <n-breadcrumb>
                    <HomeBreadcrumbItem />
                    <DiffBreadcrumbItem />
                </n-breadcrumb>
            </template>
            <template #footer>
                <n-space vertical>
                    <n-input-group>
                        <ProviderSetter :provider="inputProvider" />
                        <ReleasePairSetter :pair="inputValue" />
                        <n-button
                            type="primary"
                            @click="onGo"
                            :style="{ width: '10%' }"
                            size="large"
                        >
                            <n-icon size="large">
                                <GoIcon />
                            </n-icon>
                        </n-button>
                    </n-input-group>
                    <ProducerOptionsSetter :options="inputOptions" />
                </n-space>
            </template>
        </n-page-header>

        <iframe
            :src="`${store.state.api.baseUrl}/data/differing`"
            :style="{ 'border-width': '0px', 'width': '100%', 'height': '600px' }"
        ></iframe>
    </n-space>
</template>