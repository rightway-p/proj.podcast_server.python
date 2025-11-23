import {
  Button,
  FormControl,
  FormLabel,
  Input,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Text,
  Select,
  Stack,
  Switch,
} from '@chakra-ui/react';
import { useEffect, useMemo, useState } from 'react';
import type { CastopodPodcast, DashboardChannel, PlaylistFormInput } from '../../api/types';

interface PlaylistModalProps {
  isOpen: boolean;
  onClose: () => void;
  channels: DashboardChannel[];
  onSubmit: (payload: PlaylistFormInput) => Promise<void>;
  castopodPodcasts: CastopodPodcast[];
  onFetchCastopodPodcasts: () => Promise<void>;
  isFetchingCastopod?: boolean;
}

export function PlaylistModal({
  isOpen,
  onClose,
  channels,
  onSubmit,
  castopodPodcasts,
  onFetchCastopodPodcasts,
  isFetchingCastopod = false,
}: PlaylistModalProps) {
  const defaultChannelId = useMemo(() => channels[0]?.id ?? 0, [channels]);
  const initialForm: PlaylistFormInput = useMemo(
    () => ({
      channel_id: defaultChannelId,
      youtube_playlist_id: '',
      is_active: true,
      castopod_slug: '',
      castopod_uuid: '',
    }),
    [defaultChannelId],
  );
  const [form, setForm] = useState<PlaylistFormInput>(initialForm);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    if (!channels.length) return;
    setForm((prev) => {
      if (prev.channel_id && channels.some((channel) => channel.id === prev.channel_id)) {
        return prev;
      }
      return { ...prev, channel_id: defaultChannelId };
    });
  }, [channels, defaultChannelId, isOpen]);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await onSubmit({
        ...form,
        title: form.title?.trim() || undefined,
        castopod_slug: form.castopod_slug?.trim() || undefined,
        castopod_uuid: form.castopod_uuid?.trim() || undefined,
      });
      setForm(initialForm);
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>플레이리스트 추가</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <Stack spacing={4}>
            <FormControl isRequired>
              <FormLabel>채널</FormLabel>
              <Select value={form.channel_id} onChange={(e) => setForm({ ...form, channel_id: Number(e.target.value) })}>
                {channels.map((channel) => (
                  <option key={channel.id} value={channel.id}>
                    {channel.title}
                  </option>
                ))}
              </Select>
            </FormControl>
            <FormControl isRequired>
              <FormLabel>YouTube Playlist ID or URL</FormLabel>
              <Input
                value={form.youtube_playlist_id}
                onChange={(e) => setForm({ ...form, youtube_playlist_id: e.target.value })}
                placeholder="PL... 혹은 전체 URL"
              />
            </FormControl>
            <FormControl>
              <FormLabel>표시 이름 (선택)</FormLabel>
              <Input value={form.title ?? ''} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            </FormControl>
            <FormControl>
              <FormLabel>Castopod 채널 Slug</FormLabel>
              <Input value={form.castopod_slug ?? ''} onChange={(e) => setForm({ ...form, castopod_slug: e.target.value })} placeholder="예: rw_test2" />
            </FormControl>
            <FormControl>
              <FormLabel>Castopod 재생목록 UUID</FormLabel>
              <Input value={form.castopod_uuid ?? ''} onChange={(e) => setForm({ ...form, castopod_uuid: e.target.value })} placeholder="예: 5ed6b8d2-..." />
            </FormControl>
            <FormControl>
              <FormLabel>Castopod 목록 불러오기</FormLabel>
              <Stack spacing={2}>
                <Button size="sm" onClick={onFetchCastopodPodcasts} isLoading={isFetchingCastopod}>
                  Castopod DB 조회
                </Button>
                <Select
                  placeholder={
                    castopodPodcasts.length ? 'Castopod 재생목록을 선택하세요' : '위 버튼으로 목록을 불러와 선택하세요'
                  }
                  value={form.castopod_uuid ?? ''}
                  onChange={(e) => setForm({ ...form, castopod_uuid: e.target.value })}
                  isDisabled={!castopodPodcasts.length}
                >
                  {castopodPodcasts.map((podcast) => (
                    <option key={podcast.id} value={podcast.uuid}>
                      {podcast.title} ({podcast.uuid})
                    </option>
                  ))}
                </Select>
                <Text fontSize="sm" color="gray.500">
                  * Automation Service가 Castopod DB에 읽기 접속할 수 있어야 합니다.
                </Text>
              </Stack>
            </FormControl>
            <FormControl display="flex" alignItems="center">
              <FormLabel mb="0">활성</FormLabel>
              <Switch isChecked={form.is_active ?? true} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
            </FormControl>
          </Stack>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            취소
          </Button>
          <Button colorScheme="purple" onClick={handleSubmit} isLoading={submitting} isDisabled={!channels.length}>
            생성
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
