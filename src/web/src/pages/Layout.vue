<script setup lang="ts">
import { NIcon, NSpin, NLayout, NLayoutSider, NLayoutContent, NMenu, NBackTop } from 'naive-ui'
import { RouterView, useRouter } from 'vue-router'
</script>

<template>
    <n-layout>
        <n-layout-content content-style="padding: 10px">
            <suspense>
                <template #default>
                    <router-view>
                    </router-view>
                </template>
                <template #fallback>
                    <n-spin :size="80" id="loading-spin" style="width: 100%" />
                </template>
            </suspense>
            <n-back-top :right="60" />
        </n-layout-content>
    </n-layout>
    <n-back-top :right="60" />
</template>