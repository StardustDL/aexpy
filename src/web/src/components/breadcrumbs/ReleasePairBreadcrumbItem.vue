<script setup lang="ts">
import { NIcon, NBreadcrumbItem, NFlex } from 'naive-ui'
import { PackageIcon, VersionIcon } from '../icons'
import { ReleasePair } from '../../models';
import { projectUrl } from '../../services/utils'
import { computed } from 'vue';

const props = defineProps<{
    release?: ReleasePair;
}>();

const sameProject = computed(() => props.release && props.release.old.project == props.release.new.project);
</script>

<template>
    <n-breadcrumb-item v-if="release && sameProject">
        <router-link :to="projectUrl(release.old.project)">
            <n-icon :component="PackageIcon" />
            {{ release.old.project }}
        </router-link>
    </n-breadcrumb-item>
    <n-breadcrumb-item v-if="release && sameProject">
        <router-link to="#">
            <n-icon :component="VersionIcon" />
            {{ release.old.version }}..{{ release.new.version }}
        </router-link>
    </n-breadcrumb-item>
    <n-breadcrumb-item v-else>
        <router-link to="#">
            <n-icon :component="VersionIcon" />
            {{ release?.toString() ?? "Unknown" }}
        </router-link>
    </n-breadcrumb-item>
</template>