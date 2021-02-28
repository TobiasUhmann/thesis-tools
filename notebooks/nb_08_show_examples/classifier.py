from torch import Tensor
from torch.nn import EmbeddingBag, Linear, Module
from torchtext.vocab import Vocab


class Classifier(Module):
    embedding_bag: EmbeddingBag
    linear: Linear

    def __init__(self, embedding_bag: EmbeddingBag, linear: Linear):
        super().__init__()

        self.embedding_bag = embedding_bag
        self.linear = linear

    @classmethod
    def from_random(cls, vocab: Vocab, emb_size: int, class_count: int):
        embedding_bag = EmbeddingBag(num_embeddings=len(vocab), embedding_dim=emb_size)
        linear = Linear(emb_size, class_count)

        initrange = 0.5
        embedding_bag.weight.data.uniform_(-initrange, initrange)
        linear.weight.data.uniform_(-initrange, initrange)
        linear.bias.data.uniform_(-initrange, initrange)

        return cls(embedding_bag, linear)

    @classmethod
    def from_pre_trained(cls, vocab: Vocab, class_count: int, freeze=True):
        embedding_bag = EmbeddingBag.from_pretrained(vocab.vectors, freeze=freeze)
        linear = Linear(len(vocab.vectors.shape[1]), class_count)

        initrange = 0.5
        embedding_bag.weight.data.uniform_(-initrange, initrange)
        linear.weight.data.uniform_(-initrange, initrange)
        linear.bias.data.uniform_(-initrange, initrange)

        return cls(embedding_bag, linear)

    def forward(self, sents_batch: Tensor) -> Tensor:
        """
        :param sents_batch: (batch_size, sent_count, sent_len)
        :return (batch_size, class_count)
        """

        #
        # Embed sentences
        #
        # < embedding_bag.weight  (vocab_size, emb_size)
        # < sents_batch           (batch_size, sent_count, sent_len)
        # > sent_embs_batch       (batch_size, sent_count, emb_size)
        #

        sent_embs_batch = self.embed_sents(sents_batch)

        #
        # Average sentence embeddings
        #
        # < sent_embs_batch     (batch_size, sent_count, emb_size)
        # > avg_sent_emb_batch  (batch_size, emb_size)
        #

        avg_sent_emb_batch = sent_embs_batch.mean(axis=1)

        # log_tensor(sent_embs_batch.detach(), 'sent_embs_batch', [get_ent_lbls(), get_sent_lbls(), get_emb_lbls()])
        # log_tensor(avg_sent_emb_batch.detach(), 'avg_sent_emb_batch', [get_ent_lbls(), get_emb_lbls()])

        #
        # Push averaged sentence through linear layer
        #
        # < avg_sent_emb_batch  (batch_size, emb_size)
        # > logits_batch        (batch_size, class_count)
        #

        logits_batch = self.linear(avg_sent_emb_batch)

        return logits_batch

    def embed_sents(self, sents_batch: Tensor) -> Tensor:
        """
        :param sents_batch: (batch_size, sent_count, sent_len)
        :return: (batch_size, sent_count, emb_size)
        """

        #
        # Flatten batch
        #
        # < sents_batch  (batch_size, sent_count, sent_len)
        # > flat_sents   (batch_size * sent_count, sent_len)
        #

        batch_size, sent_count, sent_len = sents_batch.shape

        flat_sents = sents_batch.reshape(batch_size * sent_count, sent_len)

        #
        # Embed sentences
        #
        # < embedding_bag.weight  (vocab_size, emb_size)
        # < flat_sents            (batch_size * sent_count, sent_len)
        # > flat_sent_embs        (batch_size * sent_count, emb_size)
        #

        flat_sent_embs = self.embedding_bag(flat_sents)

        #
        # Restore batch
        #
        # < flat_sent_embs   (batch_size * sent_count, emb_size)
        # > sent_embs_batch  (batch_size, sent_count, emb_size)
        #

        _, emb_size = flat_sent_embs.shape

        sent_embs_batch = flat_sent_embs.reshape(batch_size, sent_count, emb_size)

        return sent_embs_batch
