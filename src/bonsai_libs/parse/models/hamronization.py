"""Models related to the hAMRonization format.

Kleborate implementation:
https://kleborate.readthedocs.io/en/stable/kpsc_modules.html/
hamronization-report-for-kleborate
"""

from typing import TypeAlias

from pydantic import BaseModel, Field, PositiveInt

from .base import RWModel


class BaseSequenceRecord(BaseModel):
    """Base sequence metadata shared by inputs and references.

    Contains start/stop positions and lengths for genes and proteins.
    """

    gene_start: int | None = Field(
        default=None,
        description=(
            "The position of the first nucleotide in a gene sequence."
            " Also known as the query gene start site in a BLAST search."
        ),
        examples=[18],
    )
    gene_stop: PositiveInt | None = Field(
        default=None,
        description=(
            "The position of the last nucleotide in a gene sequence."
            " Also known as the query gene stop site in a BLAST search."
        ),
        examples=[921],
    )
    gene_length: PositiveInt | None = Field(
        default=None,
        description=("The length (number of positions) of a gene sequence."),
        examples=[657],
    )
    protein_start: int | None = Field(
        default=None,
        description=(
            "The position of the first amino acid in a protein sequence."
            " Also known as the query protein start site in a BLAST search."
        ),
        examples=[6],
    )
    protein_stop: PositiveInt | None = Field(
        default=None,
        description=(
            "The position of the last amino acid in a protein sequence."
            " Also known as the query protein stop site in a BLAST search."
        ),
        examples=[307],
    )
    protein_length: PositiveInt | None = Field(
        default=None,
        description=("The length (number of positions) of a protein sequence."),
        examples=[219],
    )


class InputSequence(BaseSequenceRecord):
    """Description of the input sequence.

    Prefixed by input in the file specification."""

    file_name: str = Field(
        description="Name or other identifier of an entry from a sample database.",
        examples=["ERR3581801"],
    )
    sequence_id: str | None = Field(
        default=None,
        description="The identifier of a molecular sequence being analyzed.",
        examples=["DAAGAT010000041"],
    )


class ReferenceSequence(BaseSequenceRecord):
    """Description of the reference sequence.

    Prefixed by input in the file specification."""

    accession: str = Field(
        description="A persistent, unique identifier of a molecular sequence database entry.",
        examples=["NF000491.1"],
    )
    reference_db_id: str = Field(
        description="Database containing references genomes for genome annotation, gene identification, characterization etc.",
        examples=["ncbi", "ResFinder"],
    )
    reference_db_version: str = Field(
        description="Version of a particular database.", examples=["3.1.2"]
    )


class HamronizationEntry(RWModel):
    """hARMonization entry.

    Specification:
    https://github.com/pha4ge/hAMRonization/blob/master/docs/hAMRonization_specification_details.csv
    """

    input: InputSequence
    reference: ReferenceSequence
    strand_orientation: str | None = Field(
        default=None,
        description="The orientation of a gene in a double stranded DNA replicon.",
        examples=["+", "-", "sense", "antisense"],
    )
    gene_symbol: str = Field(
        description=(
            "The short name of a gene or gene product; a single word that does not contain"
            " white space characters. It is typically derived from the gene/gene product name."
        ),
        examples=["catA1", "blaOXA-101"],
    )
    gene_name: str = Field(
        description=(
            "The name of a gene, (typically) assigned by a person and/or according to a"
            " naming scheme. It may contain white space characters and is typically more"
            " intuitive and readable than a gene symbol. It (typically) may be used to"
            " identify similar genes in different species and to derive a gene symbol."
        ),
        examples=["type A-1 chloramphenicol O-acetyltransferase"],
    )
    coverage_depth: float | None = Field(
        default=None,
        description=(
            "Coverage (read depth or depth) is the average number of reads"
            " representing a given nucleotide in the reconstructed sequence."
        ),
        examples=[56],
    )
    coverage_percentage: float | None = Field(
        default=None,
        description=(
            "The percentage of the reference sequence covered by the sequence of"
            " interest. Range 1-100"
        ),
        examples=[90],
    )
    coverage_ratio: float | None = Field(
        default=None,
        description="The ratio of the reference sequence covered by the sequence of interest.",
        examples=["450/500"],
    )
    sequence_identity: float | None = Field(
        default=None,
        description=(
            "Sequence identity is the number (%) of matches (identical characters) in"
            " positions from an alignment of two molecular sequences."
        ),
        examples=[1],
    )
    drug_class: str | None = Field(
        default=None,
        description=(
            "A set of medications and other compounds that have similar chemical"
            " structures, the same mechanism of action (i.e., bind to the same biological"
            " target), a related mode of action, and/or are used to treat the same disease."
        ),
        examples=["Phenicol"],
    )
    antimicrobial_agent: str | None = Field(
        default=None,
        description=(
            "A substance that kills or slows the growth of microorganisms, including"
            " bacteria, viruses, fungi and protozoans."
        ),
        examples=["CHLORAMPHENICOL"],
    )
    resistance_mechanism: str | None = Field(
        default=None,
        description=(
            "Cellular processes in a pathogen that result in antimicrobial"
            " drug resistance."
        ),
        examples=["target alteration"],
    )
    analysis_software_name: str = Field(
        description="The name of a computer package, application, method or function.",
        examples=["amrfinder"],
    )
    analysis_software_version: str = Field(
        description=(
            "A version number is a unique number or set of numbers assigned to a"
            " specific release of a software program, file, firmware, device driver, or"
            " even hardware. Typically, as updates and entirely new editions of a program"
            " or driver are released, the version number will increase."
        ),
        examples=["1.2.5"],
    )
    genetic_variation_type: str = Field(
        description=(
            "The type of genetic variant (e.g. gene presence, gene absence, protein"
            " variant, nucleotide variant)."
        ),
        examples=["protein_mutation"],
    )
    variant_frequency: float | None = Field(
        default=None,
        description="The frequency of the variant in the data.",
        examples=[0.5],
    )
    nucleotide_mutation: str | None = Field(
        default=None,
        description=(
            "The nucleotide sequence change(s) detected in the sequence being analyzed"
            " compared to a reference in HGVS format."
        ),
        examples=["c.1349C>T"],
    )
    nucleotide_mutation_interpretation: str | None = Field(
        default=None,
        description=(
            "The description of the HGVS encoded nucleotide mutation(s) for clinical"
            " interpretation."
        ),
        examples=[
            "This is a subst found in rpoB at position 1349 where the reference has a C"
            " and the sample has a T"
        ],
    )
    protein_mutation: str | None = Field(
        default=None,
        description=(
            "The protein sequence change(s) detected in the sequence being analyzed"
            " compared to a reference in HGVS format."
        ),
        examples=["p.Ser450Leu"],
    )
    protein_mutation_interpretation: str | None = Field(
        default=None,
        description=(
            "The description of the HGVS encoded protein mutation(s) for clinical"
            " interpretation."
        ),
        examples=[
            "This is a amino acid subst found in rpoB at position 450 where the reference"
            " has a Serine and the sample has a Leucine"
        ],
    )


HamronizationEntries: TypeAlias = list[HamronizationEntry]
