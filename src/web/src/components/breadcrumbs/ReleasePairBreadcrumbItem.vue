<script setup lang="ts">
import { NIcon, NBreadcrumbItem, NSpace } from 'naive-ui'
import { ReleaseIcon } from '../icons'
import { RouterLink } from 'vue-router'
import { useStore } from '../../services/store'
import { Release, ReleasePair } from '../../models';

const store = useStore();

const props = defineProps<{
    release?: ReleasePair;
}>();
</script>

<template>
    <n-breadcrumb-item>
        <n-space>
            <n-icon>
                <ReleaseIcon />
            </n-icon>
            {{ props.release?.toString() ?? "Unknown" }}
        </n-space>
    </n-breadcrumb-item>
</template>