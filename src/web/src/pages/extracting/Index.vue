<script setup lang="ts">
import { ref, computed } from 'vue'
import { NPageHeader, NSpace, NText, NBreadcrumb, NIcon, NLayoutContent, NAvatar, NStatistic, NTabs, NTabPane, NCard, NButton, useOsTheme, NInput, NInputGroup } from 'naive-ui'
import { HomeIcon, RootIcon, ExtractIcon, GoIcon, ProviderIcon, ReleaseIcon } from '../../components/icons'
import { useRouter } from 'vue-router'
import HomeBreadcrumbItem from '../../components/breadcrumbs/HomeBreadcrumbItem.vue'
import ExtractBreadcrumbItem from '../../components/breadcrumbs/ExtractBreadcrumbItem.vue'
import { useStore } from '../../services/store'

const store = useStore();
const router = useRouter();

const inputProvider = ref<string>("default");
const inputValue = ref<string>("coxbuild@0.1.0");

function onGo() {
    router.push(`/extracting/${inputProvider.value}/${inputValue.value}/`);
}

</script>

<template>
    <n-page-header title="Extracting" subtitle="Aexpy" @back="() => router.back()">
        <template #avatar>
            <n-avatar>
                <n-icon>
                    <ExtractIcon />
                </n-icon>
            </n-avatar>
        </template>
        <template #header>
            <n-breadcrumb>
                <HomeBreadcrumbItem />
                <ExtractBreadcrumbItem />
            </n-breadcrumb>
        </template>
        <template #footer>
            <n-input-group>
                <n-input
                    :style="{ width: '20%' }"
                    v-model:value="inputProvider"
                    placeholder="Provider"
                >
                    <template #prefix>
                        <n-icon size="large">
                            <ProviderIcon />
                        </n-icon>
                    </template>
                </n-input>
                <n-input :style="{ width: '70%' }" v-model:value="inputValue" placeholder="Release">
                    <template #prefix>
                        <n-icon size="large">
                            <ReleaseIcon />
                        </n-icon>
                    </template>
                </n-input>
                <n-button type="primary" :style="{ width: '10%' }" ghost @click="onGo">
                    <n-icon size="large">
                        <GoIcon />
                    </n-icon>
                </n-button>
            </n-input-group>
        </template>
    </n-page-header>
</template>