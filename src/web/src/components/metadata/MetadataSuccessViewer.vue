<script setup lang="ts">
import { NIcon, NTime, NSpace, NTooltip, NTag, NAvatar, NText } from 'naive-ui'
import { FaceId, FaceIdError } from '@vicons/tabler'

const props = defineProps<{
    success: boolean,
}>();

</script>

<template>
    <n-tag :type="props.success ? 'success' : 'error'">
        <template #avatar>
            <n-icon size="medium">
                <FaceId v-if="props.success" />
                <FaceIdError v-else />
            </n-icon>
        </template>
        <span>{{ props.success ? 'Success' : 'Error' }}</span>
    </n-tag>
</template>