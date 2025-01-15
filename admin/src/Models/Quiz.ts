import Base from "./Base";

export default class Quiz extends Base<Quiz> {
    name!: string;
    description!: string;
    created_at!: string;
    updated_at!: string;
    deleted_at!: string | null;

    static model = {
        root: "/quiz/quiz",
        id: "id",
        attributes: {
            name: "",
            description: "",
            deleted_at: null,
        },
    };

    override deleteConfirmMessage() {
        return "Are you sure you want to delete this quiz?";
    }
}
