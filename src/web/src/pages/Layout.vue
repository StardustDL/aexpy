<script setup lang="ts">
import { ref, h, onMounted, onUpdated, onUnmounted } from 'vue'
import { NIcon, NSpin, NLayout, NLayoutSider, NLayoutContent, NMenu, NBackTop } from 'naive-ui'
import { HomeIcon, PreprocessIcon, ExtractIcon, DiffIcon, EvaluateIcon, ReportIcon, BatchIcon, RootIcon, CodeIcon, ViewIcon } from '../components/icons';
import { RouterView, useRouter } from 'vue-router'

const router = useRouter();

function renderIcon(icon: any) {
    return () => h(NIcon, null, { default: () => h(icon) })
}

const menuActiveKey = ref("home");

const menuOptions = [
    {
        label: "AexPy",
        key: "home",
        icon: renderIcon(RootIcon),
        route: "/",
    },
    {
        key: 'divider-1',
        type: 'divider',
    },
    {
        label: "Distribution",
        key: "distribution",
        icon: renderIcon(PreprocessIcon),
        route: "/distribution"
    },
    {
        label: "Description",
        key: "description",
        icon: renderIcon(ExtractIcon),
        route: "/description"
    },
    {
        label: "Difference",
        key: "difference",
        icon: renderIcon(DiffIcon),
        route: "/difference"
    },
    {
        label: "Report",
        key: "report",
        icon: renderIcon(ReportIcon),
        route: "/report"
    },
    {
        key: 'divider-2',
        type: 'divider',
    },
];

function updateMenuActiveKey() {
    for (const option of menuOptions) {
        if (option.route == undefined)
            continue;
        if (option.route == "/")
            continue;
        if (router.currentRoute.value.path.startsWith(option.route)) {
            menuActiveKey.value = option.key;
            return;
        }
    }
    menuActiveKey.value = "home";
}

const routerHook = ref<any>(undefined);

onMounted(() => {
    routerHook.value = router.afterEach(updateMenuActiveKey);
});
onUnmounted(() => {
    routerHook.value();
});

async function onMenuClick(key: string, item: any) {
    await router.push(item.route);
}
</script>

<template>
    <n-layout has-sider style="height: 100%;">
        <n-layout-sider
            collapse-mode="width"
            :collapsed-width="48"
            :width="200"
            show-trigger="arrow-circle"
            bordered
            :native-scrollbar="false"
            :default-collapsed="true"
        >
            <n-menu
                v-model:value="menuActiveKey"
                @update:value="onMenuClick"
                :options="menuOptions"
            />
        </n-layout-sider>
        <n-layout-content
            content-style="padding: 10px"
            :native-scrollbar="false"
        >
            <suspense>
                <template #default>
                    <router-view></router-view>
                </template>
                <template #fallback>
                    <n-spin :size="80" id="loading-spin" style="width: 100%" />
                </template>
            </suspense>
            <n-back-top :right="60" />
        </n-layout-content>
    </n-layout>
</template>