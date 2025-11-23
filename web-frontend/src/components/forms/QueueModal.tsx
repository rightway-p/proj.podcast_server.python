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
  Select,
  Stack,
  Switch,
  Text,
  Textarea,
} from '@chakra-ui/react';
import { useEffect, useMemo, useState } from 'react';
import type { Playlist, JobFormInput } from '../../api/types';

interface QueueModalProps {
  isOpen: boolean;
  onClose: () => void;
  playlists: Playlist[];
  defaultPlaylist?: Playlist;
  onSubmit: (payload: JobFormInput) => Promise<void>;
}

const actionOptions = [
  { value: 'sync', label: '전체 동기화' },
  { value: 'incremental', label: '신규 업로드만' },
];

export function QueueModal({ isOpen, onClose, playlists, defaultPlaylist, onSubmit }: QueueModalProps) {
  const fallbackPlaylist = useMemo(() => defaultPlaylist ?? playlists[0], [defaultPlaylist, playlists]);
  const initialForm: JobFormInput = useMemo(
    () => ({
      playlist_id: fallbackPlaylist?.id ?? 0,
      action: 'sync',
      castopod_slug: fallbackPlaylist?.castopod_slug ?? '',
      castopod_playlist_uuid: fallbackPlaylist?.castopod_uuid ?? '',
      note: '',
      should_castopod_upload: false,
    }),
    [fallbackPlaylist],
  );
  const [form, setForm] = useState<JobFormInput>(initialForm);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    setForm((prev) => ({
      ...prev,
      playlist_id: fallbackPlaylist?.id ?? prev.playlist_id,
      castopod_slug: fallbackPlaylist?.castopod_slug ?? '',
      castopod_playlist_uuid: fallbackPlaylist?.castopod_uuid ?? '',
      should_castopod_upload: false,
    }));
  }, [fallbackPlaylist, isOpen]);

  const handlePlaylistChange = (playlistId: number) => {
    const selected = playlists.find((playlist) => playlist.id === playlistId);
    setForm((prev) => ({
      ...prev,
      playlist_id: playlistId,
      castopod_slug: selected?.castopod_slug ?? '',
      castopod_playlist_uuid: selected?.castopod_uuid ?? '',
    }));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await onSubmit(form);
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
        <ModalHeader>작업 큐에 추가</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <Stack spacing={4}>
            <FormControl isRequired>
              <FormLabel>대상 플레이리스트</FormLabel>
              <Select
                value={form.playlist_id}
                onChange={(e) => handlePlaylistChange(Number(e.target.value))}
              >
                {playlists.map((playlist) => (
                  <option key={playlist.id} value={playlist.id}>
                    {playlist.title || playlist.youtube_playlist_id}
                  </option>
                ))}
              </Select>
            </FormControl>
            <FormControl>
              <FormLabel>작업 유형</FormLabel>
              <Select value={form.action} onChange={(e) => setForm({ ...form, action: e.target.value })}>
                {actionOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </FormControl>
            <FormControl>
              <FormLabel>Castopod 채널 Slug</FormLabel>
              <Input
                value={form.castopod_slug ?? ''}
                onChange={(e) => setForm({ ...form, castopod_slug: e.target.value })}
                placeholder="예: my-podcast"
              />
            </FormControl>
            <FormControl>
              <FormLabel>Castopod 재생목록 UUID</FormLabel>
              <Input
                value={form.castopod_playlist_uuid ?? ''}
                onChange={(e) => setForm({ ...form, castopod_playlist_uuid: e.target.value })}
                placeholder="예: b2b8c2d1-..."
              />
            </FormControl>
            <FormControl display="flex" alignItems="center">
              <FormLabel mb="0">Castopod 자동 업로드</FormLabel>
              <Switch
                isChecked={form.should_castopod_upload ?? false}
                onChange={(e) => setForm({ ...form, should_castopod_upload: e.target.checked })}
              />
            </FormControl>
            <Text fontSize="sm" color="gray.500">
              기본은 큐 완료 후 수동 업로드입니다. 자동 업로드를 원하면 위 스위치를 켜세요.
            </Text>
            <FormControl>
              <FormLabel>비고</FormLabel>
              <Textarea value={form.note ?? ''} onChange={(e) => setForm({ ...form, note: e.target.value })} />
            </FormControl>
          </Stack>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            취소
          </Button>
          <Button colorScheme="purple" onClick={handleSubmit} isLoading={submitting} isDisabled={!playlists.length}>
            큐에 추가
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
