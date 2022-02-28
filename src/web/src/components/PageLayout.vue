<script setup lang="ts">
import { computed } from 'vue'
import { NLayout, NLayoutContent, NLayoutHeader, NBackTop } from 'naive-ui'

const props = defineProps<{ scroll?: boolean }>();

const scroll = computed(() => props.scroll ?? false);
</script>

<template>
    <n-layout style="height: 100%;" v-if="scroll" :native-scrollbar="false">
        <n-layout-header bordered class="page-header">
            <slot name="header"></slot>
        </n-layout-header>
        <n-layout-content>
            <slot name="default"></slot>
        </n-layout-content>
        <n-back-top :right="100"></n-back-top>
    </n-layout>
    <n-layout style="height: 100%;" v-else>
        <n-layout-header bordered class="page-header">
            <slot name="header"></slot>
        </n-layout-header>
        <n-layout-content class="page-content-scroll" content-style="height: 100%;" :native-scrollbar="false">
            <slot name="default"></slot>
        </n-layout-content>
    </n-layout>
</template>

<style scoped>
a {
    text-decoration: none;
    color: inherit;
}

.page-header {
    height: 140px;
    padding: 10px;
}

.page-content-scroll {
    height: calc(100% - 140px);
}

@media screen and (max-width: 960px) {
    .page-header {
        height: 150px;
    }

    .page-content-scroll {
        height: calc(100% - 150px);
    }
}
</style>