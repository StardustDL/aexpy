<script setup lang="ts">
import { ref, h } from 'vue'
import { NIcon, NSpin } from 'naive-ui'
import { Home, Files } from '@vicons/tabler'
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
        icon: renderIcon(Home),
        route: "/"
    },
];

async function onMenuClick(key: string, item: any) {
    await router.push(item.route);
}
</script>

<template>
    <!--<n-layout has-sider style="height: 100%;">
        <n-layout-sider
            collapse-mode="width"
            :collapsed-width="48"
            :width="180"
            show-trigger="bar"
            bordered
            :default-collapsed="true"
            :native-scrollbar="false"
        >
            <n-menu
                v-model:value="menuActiveKey"
                @update:value="onMenuClick"
                :options="menuOptions"
            />
        </n-layout-sider>
        <n-layout-content>
            <suspense>
                <template #default>
                    <router-view></router-view>
                </template>
                <template #fallback>
                    <n-spin :size="80" id="loading-spin" style="width: 100%" />
                </template>
            </suspense>
        </n-layout-content>
    </n-layout>-->

    <suspense>
        <template #default>
            <router-view></router-view>
        </template>
        <template #fallback>
            <n-spin :size="80" id="loading-spin" style="width: 100%" />
        </template>
    </suspense>
</template>