<script setup lang="ts">
import { ref, h, onMounted, onUpdated, onUnmounted } from 'vue'
import { NIcon, NSpin, NLayout, NLayoutSider, NLayoutContent, NMenu } from 'naive-ui'
import { HomeIcon, PreprocessIcon, ExtractIcon, DiffIcon, EvaluateIcon, ReportIcon, BatchIcon } from '../components/icons';
import { RouterView, useRouter } from 'vue-router'

const router = useRouter();

function renderIcon(icon: any) {
    return () => h(NIcon, null, { default: () => h(icon) })
}

const menuActiveKey = ref("home");

const menuOptions = [
    {
        label: "Home",
        key: "home",
        icon: renderIcon(HomeIcon),
        route: "/"
    },
    {
        label: "Preprocess",
        key: "preprocess",
        icon: renderIcon(PreprocessIcon),
        route: "/preprocessing"
    },
    {
        label: "Extract",
        key: "extract",
        icon: renderIcon(ExtractIcon),
        route: "/extracting"
    },
    {
        label: "Diff",
        key: "diff",
        icon: renderIcon(DiffIcon),
        route: "/differing"
    },
    {
        label: "Evaluate",
        key: "evaluate",
        icon: renderIcon(EvaluateIcon),
        route: "/evaluating"
    },
    {
        label: "Report",
        key: "report",
        icon: renderIcon(ReportIcon),
        route: "/reporting"
    },
    {
        label: "Batch",
        key: "batch",
        icon: renderIcon(BatchIcon),
        route: "/batching"
    },
];

function updateMenuActiveKey() {
    for (const option of menuOptions) {
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
            show-trigger="bar"
            bordered
            :native-scrollbar="false"
        >
            <n-menu
                v-model:value="menuActiveKey"
                @update:value="onMenuClick"
                :options="menuOptions"
            />
        </n-layout-sider>
        <n-layout-content
            content-style="padding: 10px; padding-left: 20px;"
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
        </n-layout-content>
    </n-layout>
</template>